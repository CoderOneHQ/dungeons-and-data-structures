import multiprocessing
import time
import logging

from ..agent import Agent as AIAgent, GameState, PlayerState
from .agent import Agent
from .simple_driver import Driver as SimpleDriver


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class StateUpdate:
	def __init__(self, game=None, player=None):
		self.game = game
		self.player = player

class GameOver:
	def __init__(self, game=None, player=None):
		self.game = game
		self.player = player

class AgentProxy(Agent):
	def __init__(self, task_queue, result_queue, name:str):
		logger.debug("Creating multiproc agent proxy for %s", name)
		self.name = name
		self.task_queue = task_queue
		self.result_queue = result_queue
		self.silenced = False
	
	def stop(self):
		self.task_queue.put(None)

	def next_move(self):
		return self.result_queue.get_nowait() if not self.result_queue.empty() else None
	
	def update(self, game_state:GameState, player_state:PlayerState):
		self.task_queue.put_nowait(StateUpdate(game=game_state, player=player_state))

	def on_game_over(self, game_state:GameState, player_state:PlayerState):
		self.task_queue.put_nowait(GameOver(game=game_state, player=player_state))

	# def next_move(self, game_map, game_state):
	# 	try:
	# 		move = self.result_queue.get_nowait() if not self.result_queue.empty() else None
	# 		self.task_queue.put_nowait(StateUpdate(game=game_map, state=game_state))
	# 		return move
	# 	except Exception as e:
	# 		#self.agent = None # Stop existing agent untill the module is fixed
	# 		if not self.silenced:
	# 			# self.silenced = True
	# 			logger.error(f"Agent '{self.name}' error: {e}", exc_info=True)
	# 	return None


class Consumer(multiprocessing.Process):
	def __init__(self, task_queue, result_queue, module_name:str, watch:bool, config):
		multiprocessing.Process.__init__(self, daemon=True)
		self.task_queue = task_queue
		self.result_queue = result_queue
		self.module_name = module_name
		self.watch = watch
		self.config = config

		self.is_not_done = True
		self.game_state = None
		self.player_state = None

	def _process_cmd(self, cmd):
		if not cmd: # Poison pill means shutdown
			self.is_not_done = True
			self.task_queue.close()
			self.result_queue.close()
			logger.debug(f'Agent {self.name}: Exiting')
			return False

		if isinstance(cmd, StateUpdate):
			self.game_state = cmd.game
			self.player_state = cmd.player
		else:
			logger.error(f"Unexpected command {cmd}")

		return True


	def run(self):
		driver = SimpleDriver(self.module_name, watch=self.watch, config=self.config)
		
		try:
			agent = driver.agent()

			time_posted = time.time()
			while self.is_not_done:
				while not self.task_queue.empty():
					cmd = self.task_queue.get()
					if not self._process_cmd(cmd):
						continue

				if self.game_state and self.player_state:
					cycle_start_time = time.time()
	
					agent_action = agent.next_move(self.game_state, self.player_state)

					self.game_map = None
					self.game_state = None

					self.result_queue.put(agent_action)				

					logger.debug(f"Time since last post: {cycle_start_time - time_posted}")
					time_posted = cycle_start_time

		except OSError:
			pass
		
		except KeyboardInterrupt:
			pass

		logger.debug(f"{self.name} loop is over")
		return


class Driver:

	JOIN_TIMEOUT_SEC = 1

	def __init__(self, name:str, watch: bool = False, config={}):
		self.name = name
		self.watch = watch
		self.config = config
		self._proxies = []
		self._workers = []

	def stop(self):
		for p in self._proxies:
			p.stop()

		for w in self._workers:
			try:
				w.join(self.JOIN_TIMEOUT_SEC)
				w.close()
			except ValueError:
				logger.warn(f"process for agent '{self.name}' has not finished gracefully. Terminating")
				w.terminate()

	def agent(self):
		tasks_queue = multiprocessing.Queue()
		agent_result_queue = multiprocessing.Queue()
		proxy = AgentProxy(tasks_queue, agent_result_queue, self.name)

		worker = Consumer(tasks_queue, agent_result_queue, self.name, self.watch, self.config)
		worker.start()

		self._workers.append(worker)
		self._proxies.append(proxy)
		return proxy

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()
