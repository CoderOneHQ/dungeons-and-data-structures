import importlib

from .agent import ModuleProxy
from .module_watcher import ModuleWatcher

class Driver:

	def __init__(self, name:str, watch: bool = False, config={}):
		self.name = name
		self.watcher = name
		self.agent_module = importlib.import_module(name)
		
		if watch:
			proxy = ModuleProxy(self.agent_module)
			
			self.watcher = ModuleWatcher()
			self.watcher.watch_module(self.agent_module, proxy.on_reload)
			self.watcher.start_watching()

			self.agent_module = proxy

	def stop(self):
		if self.watcher:
			self.watcher.stop_watching()

	def agent(self):
		return self.agent_module.agent() if self.agent_module else None
