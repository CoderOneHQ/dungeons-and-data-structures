import jsonplus
from .game import Recorder, GameEvent, GameSysAction, PlayerMove

class FileRecorder(Recorder):
	""" A game recording that saves the game into a file
	"""
	def __init__(self, file_name:str):
		self.file = open(file_name, mode='wt')

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if self.file:
			self.file.close()
			self.file = None	

	def record(self, tick:int, event: GameEvent):
		self.file.write(f"{tick}: ")

		if isinstance(event, GameSysAction):
			self.file.write(f"{event.action.value} ")
			self.file.write(jsonplus.dumps(event.payload))
		
		elif isinstance(event, PlayerMove):
			self.file.write(f"{event.pid} {event.action.value}")

		self.file.write("\n")
		self.file.flush()

