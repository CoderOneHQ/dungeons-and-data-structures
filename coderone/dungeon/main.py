#!/usr/bin/env python
"""
 Dungeons & Data Structures
 Coder One AI game tournament challenge
"""

import argparse
import os
import sys
import logging
import jsonplus
from contextlib import ExitStack
from typing import Dict, List, Tuple, Union, NamedTuple, Any, Optional

from appdirs import user_config_dir

from .game_recorder import FileRecorder, Recorder
# from coderone.dungeon.agent_driver.simple_driver import Driver
from .agent_driver.multiproc_driver import Driver

from .game import Game

APP_NAME = 'coderone.dungeon'

ASSET_DIRECTORY = os.path.join(os.path.dirname(__file__), 'assets')
DEFAULT_CONFIG_FILE = 'config.json'


SCREEN_TITLE = "Coder One: Dungeons & Data Structures"


TICK_STEP = 0.1 			# Number of seconds per 1 iteration of game loop
ITERATION_LIMIT = 180*10 	# Max number of iteration the game should go on for, None for unlimited

logger = logging.getLogger()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# logger.setLevel(logging.DEBUG)


def __load_or_generate_config(config_file:Optional[str]) -> dict:
	## Setting up the players using the config file

	if config_file:
		# A custom config file location given:
		try:
			with open(config_file) as f:
				config_data = jsonplus.loads(f.read())
		except: # Failed to load config, fallback to default values
			logger.error(f"config file '{config_file}' not found, using default value")
			raise
	else:
		# Default config file expected:
		config_dir = user_config_dir(APP_NAME)
		config_file = os.path.join(config_dir, DEFAULT_CONFIG_FILE)

		try:
			with open(config_file) as f:
				config_data = jsonplus.loads(f.read())
		except FileNotFoundError: # Failed to load config, fallback to default values
			logger.warning(f"No default config file found, generating...")
			config_data = {
				"headless": False,
				"interactive": False,
				"start_paused": True,
				"wait_end": 5,
				"max_iterations": ITERATION_LIMIT,
				"tick_step": TICK_STEP
			}

			os.makedirs(config_dir, exist_ok=True)
			logger.warning(f"Writing default config into: {config_file}")
			with open(config_file, "w") as f:
				f.write(jsonplus.pretty(config_data))
		
	
	config_data.setdefault('start_paused', False)
	config_data.setdefault('wait_end', 10)
	config_data.setdefault('assets', ASSET_DIRECTORY)
	config_data.setdefault('interactive', False)
	config_data.setdefault('tick_step', TICK_STEP)
	config_data.setdefault('no_text', False)  # A work around Pillow (Python image library) bug	
	config_data.setdefault('single_step', False)
	config_data.setdefault('endless', False)
	
	config_data.setdefault('rows', Game.ROW_COUNT)
	config_data.setdefault('columns', Game.COLUMN_COUNT)
	config_data.setdefault('max_iterations', ITERATION_LIMIT)

	return config_data


# Borrowed from flask!
def _prepare_import(path):
	"""Given a filename this will try to calculate the python path, add it
	to the search path and return the actual module name that is expected.
	"""
	path = os.path.realpath(path)
	fname, ext = os.path.splitext(path)
	if ext == ".py":
		path = fname

	if os.path.basename(path) == "__init__":
		path = os.path.dirname(path)

	module_name = []

	# move up until outside package structure (no __init__.py)
	while True:
		path, name = os.path.split(path)
		module_name.append(name)

		if not os.path.exists(os.path.join(path, "__init__.py")):
			break

	if sys.path[0] != path:
		sys.path.insert(0, path)

	return ".".join(module_name[::-1])


def __load_agent_drivers(cntx: ExitStack, agent_modules, config:dict, watch=False):
	agents = []
	n_agents = len(agent_modules)

	logger.info(f"Loading agent modules: {n_agents} required")
	for counter, agent_module in enumerate(agent_modules):
		try:
			logger.info(f"[{counter + 1}/{n_agents}] loading agent driver: {agent_module}")
			module_name = _prepare_import(agent_module)
			driver = Driver(module_name, watch, config)
			cntx.enter_context(driver)
			agents.append(driver)
		except Exception as e:
			logger.error(f"failed to load agent module {agent_module}")
			logger.error(e, exc_info=True)
			return None
	
	return agents

class TooManyPlayers(Exception):
	pass

def run(agent_modules, player_names, config=None, recorder=None, watch=False):
	# Create a new game
	row_count = config.get('rows')
	column_count = config.get('columns')
	iteration_limit = config.get('max_iterations')
	is_interactive = config.get('interactive')

	# Check max number of players support by the map:
	squers_per_player = 6
	max_players = row_count*column_count / squers_per_player
	if max_players < len(agent_modules):
		raise TooManyPlayers(f"Game map ({column_count}x{row_count}) supports at most {max_players} players while {len(agent_modules)} agent requested.")


	# Load agent modules
	with ExitStack() as stack:
		agents = __load_agent_drivers(stack, agent_modules, watch=watch, config=config)
		if not agents:
			return None  # Exiting with an error, no contest

		game = Game(row_count=row_count, column_count=column_count, max_iterations=iteration_limit, recorder=recorder)

		# Add all agents to the game
		names_len = len(player_names) if player_names else 0
		for i, agent_driver in enumerate(agents):
			game.add_agent(agent_driver.agent(), player_names[i] if i < names_len else agent_driver.name)

		# Add a player for the user if running in interactive mode or configured interactive
		user_pid = game.add_player("Player") if is_interactive else None

		game.generate_map()

		tick_step = config.get('tick_step')
		if config.get('headless'):
			from .headless_client import Client

			client = Client(game=game, config=config)
			client.run(tick_step)
		else:
			if config.get('hack'):
				from .hack_client import Client
				screen_width =  80
				screen_height = 24
			else:
				from .arcade_client import Client, WIDTH, HEIGHT, PADDING
			
				screen_width =  PADDING[0]*2 + WIDTH * 12
				screen_height = PADDING[1]*3 + HEIGHT * 10

			window = Client(width=screen_width, height=screen_height, title=SCREEN_TITLE, game=game, config=config, interactive=is_interactive, user_pid=user_pid)
			window.run(tick_step)

		# Announce game winner and exit
		return game.stats


def run_match(agents:List[str], players:List[str]=None, config_name:str=None, record_file:str=None, watch:bool=False, args:Any=None):
	config = __load_or_generate_config(config_name)
	if args:
		if args.headless or 'headless' not in config:			config['headless'] = args.headless
		if args.interactive or 'interactive' not in config:		config['interactive'] = args.interactive
		if args.hack or 'hack' not in config:					config['hack'] = args.hack
		if args.no_text or 'no_text' not in config:				config['no_text'] = args.no_text
		if args.start_paused or 'start_paused' not in config:	config['start_paused'] = args.start_paused
		if args.single_step or 'single_step' not in config:		config['single_step'] = args.single_step
		if args.endless or 'endless' not in config:				config['endless'] = args.endless
		
		# if args.watch or 'watch' not in config:					config['watch'] = args.watch
		# if args.record or 'record' not in config:				config['record'] = args.record
		# if args.wait_end or 'wait_end' not in config:			config['wait_end'] = args.wait_end
		# if args.tick_step or 'tick_step' not in config:			config['tick_step'] = args.tick_step

	recorder = FileRecorder(record_file) if record_file else Recorder()

	# Everything seems in order - lets start the game
	with recorder:
		return run(agent_modules=agents, player_names=players, config=config, recorder=recorder, watch=watch)


def submit_agent(agent_module:str):
	""" Submit agent module for the team entry into the tournament.
	"""
	path = os.path.realpath(agent_module)
	fname, ext = os.path.splitext(path)
	if ext == ".py": # A single file with .py extention specified
		module_name = os.path.basename(fname)
		single = True
		if not os.path.exists(path):
			print(f"Error: specfied file not found '{agent_module}'\n"
			"No files submitted.", file=sys.stderr)
			return
	elif not ext and os.path.exists(f'{path}.py'):
		module_name = os.path.basename(fname)
		path = f'{path}.py'
		single = True
	else:
		module_name = agent_module
		single = False
		if not os.path.exists(path):
			print(f"Error: directory found for the specified module: '{agent_module}'\n"
			"No files submitted.", file=sys.stderr)
			return

	# Make sure there is a valid __init__.py if its a module:
	if not single:
		if not os.path.exists(os.path.join(path, '__init__.py')):
			print(f"Error, specfied location '{agent_module}' is a directory, but does not appear to be a properly-formed python module.\n"
			"Check the path or add missing '__init__.py' file.\n"
			"No files submitted.", 
			file=sys.stderr)
			return

	from .publisher import submit
	try:
		submit(agent_module=module_name, single=single, source_file=path)
	except KeyboardInterrupt:
		# print("Canceled.")
		return


def main():
	parser = argparse.ArgumentParser(description=SCREEN_TITLE)
	
	parser.add_argument('--headless', action='store_true',
					default=False,
					help='run without graphics')
	parser.add_argument('--interactive', action='store_true',
					default=False,
					help='all a user to contol a player')
	parser.add_argument('--no_text', action='store_true',
					default=False,
					help='Graphics bug workaround - disables all text')
	parser.add_argument('--players', type=str,
					help="Comma-separated list of player names")
	parser.add_argument('--hack', action='store_true',
					default=False,
					help=argparse.SUPPRESS)
	parser.add_argument('--start_paused', action='store_true',
					default=False,
					help='Start a game in pause mode, only if interactive')
	parser.add_argument('--single_step', action='store_true',
					default=False,
					help='Game will run one step at a time awaiting for player input')
	parser.add_argument('--endless', action='store_true',
					default=False,
					help='Game will restart after the match is over. indefinitely')

	parser.add_argument('--submit', action='store_true',
					default=False,
					help="Don't run the game, but submit the agent as team entry into the trournament")

	parser.add_argument('--record', type=str,
					help='file name to record game')
	parser.add_argument('--watch', action='store_true',
					default=False,
					help='automatically reload agents on file changes')
	parser.add_argument('--config', type=str,
					default=None,
					help='path to the custom config file')

	parser.add_argument("agents", nargs="+", help="agent module")

	args = parser.parse_args()

	n_agents = len(args.agents)
	if args.submit:
		if n_agents > 1:
			print(
				"Error: Only a single agent entry per team is allowed.\n"
				f"You have specified {n_agents} agent modules.\n"
				"Please chose only one you wish submit and try again.\n"
				, file=sys.stderr)
			sys.exit(1)

		submit_agent(agent_module=args.agents[0])
		sys.exit(0)

	if n_agents < 2 and (args.headless or not args.interactive):
		print("At least 2 agents must be provided in the match mode. Exiting", file=sys.stderr)
		sys.exit(1)

	if args.headless and args.interactive:
		print("Interactive play is not support in headless mode. Exiting", file=sys.stderr)
		sys.exit(1)
		# TODO: Do we need an error message for 'single_step' if running headless?
	if args.headless and args.no_text:
		print("Makes no sense to run headless and ask for no-text. Ignoring", file=sys.stderr)
	if not args.interactive and args.start_paused:
		print("Can not start paused in non-interactive mode. Exiting", file=sys.stderr)
		sys.exit(1)		

	jsonplus.prefer_compat()

	players = args.players.split(',') if args.players else None

	try:
		result = run_match(agents=args.agents, players=players, config_name=args.config, record_file=args.record, watch=args.watch, args=args)
		print(jsonplus.pretty(result))
	except TooManyPlayers as ex:
		print(f'Too many players for the game.\n{ex}', file=sys.stderr)
		sys.exit(1)		


	# We done here, all good.
	sys.exit(0)


if __name__ == "__main__":
	main()
