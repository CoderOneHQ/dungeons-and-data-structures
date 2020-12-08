import logging
from ..agent import Agent as AIAgent, GameState, PlayerState

logger = logging.getLogger(__name__)


class Agent:
	
	def next_move(self):
		pass
	
	def update(self, game_state:GameState, player_state:PlayerState):
		pass 

	def on_game_over(self, game_state:GameState, player_state:PlayerState):
		pass


class AgentProxy(AIAgent):
	def __init__(self, module):
		self.agent = None
		self.reload(module)

	def next_move(self, game_state:GameState, player_state:PlayerState):
		try: 
			return self.agent.next_move(game_state, player_state) if self.agent else None
		except Exception as e:
			# self.agent = None
			if not self.silinced:
				# self.silinced = True
				logger.error(f"Agent update error: {e}", exc_info=True)
		return None

	def on_game_over(self, game_state:GameState, player_state:PlayerState):
		try: 
			return self.agent.on_game_over(game_state, player_state) if self.agent else None
		except Exception as e:
			# self.agent = None
			if not self.silinced:
				# self.silinced = True
				logger.error(f"Agent game_over error: {e}", exc_info=True)
		return None

	def reload(self, module):
		logger.debug("Re-loading proxy agent for module '%s'", module.__name__)
		try:
			self.silinced = False
			if hasattr(module, 'agent'):
				self.agent = module.agent()
			elif hasattr(module, 'Agent'):
				self.agent = module.Agent()
			else:
				self.agent = None
				logger.warn(f"No agent definition found in module '%'", module.__name__)
		except Exception as e:
			self.agent = None
			logger.error(f"Failed to reload agent: {e}", exc_info=True)


class ModuleProxy:
	def __init__(self, module):
		self.agents = []
		self.on_reload(module)

	def agent(self) -> AIAgent:
		proxy = AgentProxy(self.module)
		self.agents.append(proxy)
		return proxy

	def on_reload(self, new_module):
		logger.debug("ModuleProxy reloaded")

		self.module = new_module
		for proxy in self.agents:
			proxy.reload(self.module)
