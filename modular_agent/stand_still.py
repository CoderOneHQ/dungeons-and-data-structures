'''
Exaple agent that does not do anything
'''
import time

class agent:
	ACTION_PALLET = ['']

	def __init__(self):
		""" Example of a random agent
		"""
		pass

	def next_move(self, ascii_map, state_dic):
		""" This method is called each time the agent is required to choose an action
		"""

		# Lets pretend that agent is doing some thinking
		time.sleep(1)

		return self.ACTION_PALLET[0]

