import importlib

from ..agent import Agent as AIAgent
from .agent import ModuleProxy
from .module_watcher import ModuleWatcher

class Driver:

	def __init__(self, name:str, watch: bool = False, config=None):
		self.name = name
		self.watcher = name
		
		module = importlib.import_module(name)
		self.agent_module = ModuleProxy(module)
		
		if watch:			
			self.watcher = ModuleWatcher()
			self.watcher.watch_module(module, self.agent_module.on_reload)
			self.watcher.start_watching()

	def stop(self):
		if self.watcher:
			self.watcher.stop_watching()

	def agent(self) -> AIAgent:
		return self.agent_module.agent() if self.agent_module else None

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()
