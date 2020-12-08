import logging
import importlib
from importlib.util import find_spec
import os, sys


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import RegexMatchingEventHandler

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

class FileEventHandler(FileSystemEventHandler):
# class FileEventHandler(RegexMatchingEventHandler):
	PY_REGEX = [r".*\.py$"]

	def __init__(self, module, callback):
		# super().__init__(self.PY_REGEX)
		self.module = module
		self.callback = callback

	def on_modified(self, event):
		"A file of interest has changed"
		logger.debug(f"Changes {event.event_type}: {event.src_path}")
		# if event.path not in self.mod_map: # Is it a file I know about?
		# 	return
		if event.src_path.endswith('.py'):
			self.__reload(event)

	def __reload(self, event):
		# # Find out which module is using that file
		module_name = self.module.__name__ #self.mod_map[event.path]
		
		# Try to reload the module
		try:
			logger.info(f"re-loading module: '{module_name}'")
			new_module = importlib.reload(self.module)
			if self.callback:
				logger.debug("re-setting agents")
				self.callback(new_module)

			logger.info(f"module '{module_name}' reloaded")
		except Exception as e:
			logger.warning(f"Failed to re-load module: '{self.module}'")
			logger.error(e, exc_info=True)


class ModuleWatcher():
	""" Automatically reload any modules or packages as they change
	"""

	def __init__(self):
		self.__event_observer = Observer()

	def _watch_file(self, module, callback, file_name:str, search_locations):
		"Add a watch for a specific file, and map said file to a module name"
		recursive = True if search_locations else False

		file_name = os.path.realpath(file_name)
		if not os.path.isdir(file_name):
			file_name = os.path.dirname(file_name)

		logger.debug(f"watching for {file_name} changes, recursive={recursive}")

		self.__event_observer.schedule(
			FileEventHandler(module, callback),
			file_name,
			recursive=recursive
		)
		
	def watch_module(self, module, callback):
		"Load module spec, determine which files it uses, and watch them"
		logger.info(f"setting up module watcher for '{module}'")
		module_name = module.__name__

		try:
			spec = find_spec(module_name)
			if spec and spec.has_location:
				self._watch_file(module, callback, spec.origin, spec.submodule_search_locations)
			else:
				logger.info(f"...skipping watcher for '{module_name}' as no spec found")
		except Exception as e:
			logger.warning(f"Failed set up watcher for module '{module_name}'")
			logger.error(e, exc_info=True)

	def start_watching(self):
		"Start watch thread"
		logger.debug("Starting file watcher")
		self.__event_observer.start()

	def stop_watching(self):
		"Stop the watching thread"
		logger.debug("stopping file watcher")
		self.__event_observer.stop()
		self.__event_observer.join()
