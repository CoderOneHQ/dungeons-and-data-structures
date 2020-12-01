'''
Example of a random agent
'''
import time
import random

class agent:
	""" Example of a random agent
	"""

	ACTION_PALLET = ['', 'u','d','l','r','p', '']

	def __init__(self):
		self.name = "random bot"
		""" Your agent initialization code goes here.
		"""

	def next_move(self, ascii_map, state_dic):
		""" This method is called each time the agent is required to choose an action
		"""
		
		return random.choice(self.ACTION_PALLET)