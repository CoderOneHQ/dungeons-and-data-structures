#!/usr/bin/env python
"""
 Dungeons & Data Structures
 fun game on a grid
"""

import argparse
import os
import time
import sys
import logging
import json
from typing import Dict, List, Tuple, Union, NamedTuple, Any, Optional

# from agent_driver.simple_driver import Driver
from agent_driver.multiproc_driver import Driver

from game import Game, GameEvent, GameSysAction, PlayerMove, Recorder
from arcade_client import MyGame, MARGIN, WIDTH, HEIGHT, PADDING


SCREEN_TITLE = "Dungeons & Data Structures"
# Do the math to figure out our screen dimensions
SCREEN_WIDTH =  PADDING[0]*2 + (WIDTH + MARGIN) * 12 + MARGIN
SCREEN_HEIGHT = PADDING[1]*3 + (HEIGHT + MARGIN) * 10 + MARGIN


# Time for each round
TIME_INTERVAL = 0.1 # it means 1 second here
ITERATION_LIMIT = 3*60*10 # Max number of iteration the game should go on for

logger = logging.getLogger()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# logger.setLevel(logging.DEBUG)


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
			self.file.write(json.dumps(event.payload))
		
		elif isinstance(event, PlayerMove):
			self.file.write(f"{event.pid} {event.action.value}")

		self.file.write("\n")
		self.file.flush()


def main(agent_modules, headless=False, watch=False, interactive=False, config_file="config.json", recorder=None):
	## Setting up the players using the config file
	try:
		with open(config_file) as f:
			config_data = json.load(f)
	except: # Failed to load config, fallback to default values
		logger.error(f"config file '{config_file}' not found, using default value")
		config_data = {}
		
	config_data.setdefault('update_time_step', TIME_INTERVAL)
	config_data.setdefault('no_text', False)  # A work around Pillow (Python image library) bug	
	
	# Load agent modules
	agents = []
	n_agents = len(agent_modules)
	logger.info(f"Loading agent modules: {n_agents} required")

	for counter, agent_module in enumerate(agent_modules):
		try:
			logger.info(f"[{counter + 1}/{n_agents}] loading agent driver: {agent_module}")
			driver = Driver(agent_module, watch, config_data)
			agents.append(driver)
		except Exception as e:
			logger.error(f"failed to load agent module {agent_module}")
			logger.error(e, exc_info=True)
			sys.exit(1)

	# Create a new game
	row_count = config_data.get('rows', Game.ROW_COUNT)
	column_count = config_data.get('columns', Game.COLUMN_COUNT)
	iteration_limit = config_data.get('max_iterations', ITERATION_LIMIT)

	game = Game(row_count=row_count, column_count=column_count, max_iterations=iteration_limit, recorder=recorder)

	# Add all agents to the game
	for agent_driver in agents:
		game.add_agent(agent_driver.agent(), agent_driver.name)

	# Add a player for the user if running in interactive mode or configured interactive
	if n_agents < 2 or interactive or config_data.get('interactive', False):
		user_pid = game.add_player("Player")
	else:
		user_pid = None

	game.generate_map()

	update_time_step = config_data.get('update_time_step')
	if headless or config_data.get('headless'):
		while not game.game_ended:
			logger.info(f"Game step [{game.tick_counter}/{game.max_iterations}]... ")

			cycle_start_time = time.time()
			game.tick(update_time_step)
			dt = time.time() - cycle_start_time

			stats = game.stats()
			for p in stats['players'].values():
				name = "{}{}".format(p['name'], '(bot)' if p['is_bot'] else "")
				logger.info(f"{name} HP: {p['hp']} / Ammo: {p['ammo']} / Score: {p['score']}, loc: ({p['position'][0]}, {p['position'][0]})")

			logger.debug(f"...step [{game.tick_counter}/{game.max_iterations}] completed in {dt*1000.0:.4f}ms")

			sleep_time = update_time_step - dt
			if sleep_time > 0:
				logger.debug(f"has time to sleep for {sleep_time}sec")
				time.sleep(sleep_time)

	else:
		window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, game, user_pid, config_data)
		window.run(update_time_step)

	# Announce game winner and exit
	results = game.stats()
	print(json.dumps(results, indent=4, sort_keys=True))

	# Clean up all agents:
	for agent_driver in agents:
		agent_driver.stop()

	# We done here, all good.
	sys.exit(0)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=SCREEN_TITLE)
	
	parser.add_argument('--headless', action='store_true',
					default=False,
					help='run without graphics')
	parser.add_argument('--interactive', action='store_true',
					default=False,
					help='all a user to contol a player')
	parser.add_argument('--watch', action='store_true',
					default=False,
					help='automatically reload agents on file changes')
	parser.add_argument('--record', type=str,
					help='file name to record game')
	parser.add_argument('--config', type=str, 
					default='config.json',
					help='path to the custom config file')

	parser.add_argument("agents", nargs="+", help="agent module")

	args = parser.parse_args()

	if args.headless and len(args.agents) < 2:
		print("At least 2 agents must be provided in the match mode. Exiting", file=sys.stderr)
		sys.exit(1)

	recorder = FileRecorder(args.record) if args.record else Recorder()

	# Everything seems in order - lets start the game
	with recorder:
		main(args.agents, headless=args.headless, watch=args.watch, interactive=args.interactive, recorder=recorder, config_file=args.config)
