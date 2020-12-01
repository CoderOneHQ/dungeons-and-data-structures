import logging

logger = logging.getLogger(__name__)


class Agent:
	def next_move(self, game_map, game_state):
		pass
	
	def stop(self):
		pass

class AgentProxy(Agent):
	def __init__(self, module):
		self.reload(module)

	def next_move(self, game_map, game_state):
		try: 
			return self.agent.next_move(game_map, game_state) if self.agent else None
		except Exception as e:
			# self.agent = None
			if not self.silinced:
				# self.silinced = True
				logger.error(f"Agent error: {e}", exc_info=True)
		return None

	def reload(self, module):
		logger.debug("Re-setting proxy agent for module '%s'", module.__name__)
		try:
			self.silinced = False
			self.agent = module.agent()
		except Exception as e:
			self.agent = None
			logger.error(f"Failed to reload agent: {e}", exc_info=True)


class ModuleProxy:
	def __init__(self, module):
		self.agents = []
		self.on_reload(module)

	def agent(self):
		proxy = AgentProxy(self.module)
		self.agents.append(proxy)
		return proxy

	def on_reload(self, new_module):
		logger.debug("ModuleProxy reloaded")

		self.module = new_module
		for proxy in self.agents:
			proxy.reload(self.module)
