import multiprocessing
import time
import logging

from .simple_driver import Driver as SimpleDriver


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class StateUpdate:
	def __init__(self, game=None, state=None):
		self.game = game
		self.state = state


class AgentProxy:
	def __init__(self, task_queue, result_queue, name:str):
		logger.debug("Creating multiproc agent proxy for %s", name)
		self.name = name
		self.task_queue = task_queue
		self.result_queue = result_queue
		self.silenced = False
	
	def stop(self):
		self.task_queue.put(None)

	def next_move(self, game_map, game_state):
		try:
			self.task_queue.put_nowait(StateUpdate(game=game_map, state=game_state))
			return self.result_queue.get_nowait() if not self.result_queue.empty() else None
		except Exception as e:
			#self.agent = None # Stop existing agent untill the module is fixed
			if not self.silenced:
				# self.silenced = True
				logger.error(f"Agent '{self.name}' error: {e}", exc_info=True)
		return None


class Consumer(multiprocessing.Process):
	def __init__(self, task_queue, result_queue, module_name:str, watch:bool, config):
		multiprocessing.Process.__init__(self, daemon=True)
		self.task_queue = task_queue
		self.result_queue = result_queue
		self.module_name = module_name
		self.watch = watch
		self.config = config

		self.is_not_done = True
		self.game_map = None
		self.game_state = None

	def _process_cmd(self, cmd):
		if not cmd: # Poison pill means shutdown
			self.task_queue.close()
			self.result_queue.close()
			self.is_not_done = True
			logger.debug(f'Agent {self.name}: Exiting')
			return False

		if isinstance(cmd, StateUpdate):
			self.game_map = cmd.game
			self.game_state = cmd.state
		else:
			logger.error(f"Unexpected command {cmd}")

		return True


	def run(self):
		driver = SimpleDriver(self.module_name, watch=self.watch, config=self.config)
		agent = driver.agent()
		
		try:
			time_posted = time.time()
			while self.is_not_done:
				if self.task_queue.empty():
					cmd = self.task_queue.get()
					if not self._process_cmd(cmd):
						continue
				else:
					while not self.task_queue.empty():
						cmd = self.task_queue.get()
						if not self._process_cmd(cmd):
							continue

				if self.game_map and self.game_state:
					cycle_start_time = time.time()
	
					agent_action = agent.next_move(self.game_map, self.game_state)
					self.result_queue.put(agent_action)
					
					self.game_map = None
					self.game_state = None

					logger.debug(f"Time since last post: {cycle_start_time - time_posted}")
					time_posted = cycle_start_time

		except OSError:
			pass

		logger.debug(f"{self.name} loop is over")
		return

class Driver:

	def __init__(self, name:str, watch: bool = False, config={}):
		self.name = name
		self.watch = watch
		self.config = config
		self._proxies = []

	def stop(self):
		for p in self._proxies:
			p.stop()

	def agent(self):
		tasks_queue = multiprocessing.Queue()
		agent_result_queue = multiprocessing.Queue()
		proxy = AgentProxy(tasks_queue, agent_result_queue, self.name)

		worker = Consumer(tasks_queue, agent_result_queue, self.name, self.watch, self.config)
		worker.start()

		self._proxies.append(proxy)
		return proxy

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()
