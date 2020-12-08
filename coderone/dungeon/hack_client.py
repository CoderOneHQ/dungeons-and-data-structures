import time
import logging

import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle

from .game import PlayerActions, Point, PID, Game

logger = logging.getLogger(__name__)


class Client:
	def __init__(self, width:int, height:int, title:str, game=None, config=None, interactive:bool=False, user_pid:PID=None):
		self.title = title
		self.game = game
		self.config = config
		self.interactive = interactive

	def _update(self, tick_step):
		self.game.tick(tick_step)

		stats = self.game.stats()
		for p in stats['players'].values():
			name = "{}{}".format(p['name'], '(bot)' if p['is_bot'] else "")
			logger.info(f"{name} HP: {p['hp']} / Ammo: {p['ammo']} / Score: {p['score']}, loc: ({p['position'][0]}, {p['position'][0]})")

	def run(self, tick_step):
		wrapper(lambda src: self.main(src, tick_step))

	def main(self, stdscr, tick_step):
		stdscr.addstr(0, 0, self.title)

		editwin = curses.newwin(5,30, 2,1)
		rectangle(stdscr, 1,0, 1+5+1, 1+30+1)
		stdscr.refresh()

		box = Textbox(editwin)

		# Let the user edit until Ctrl-G is struck.
		box.edit()

		# Get resulting contents
		message = box.gather()

	def _run(self, tick_step):
		try:
			while not self.game.is_over:
				logger.info(f"Game step [{self.game.tick_counter}/{self.game.max_iterations}]... ")
				
				cycle_start_time = time.time()
				self._update(tick_step)
				dt = time.time() - cycle_start_time
				logger.debug(f"...step [{self.game.tick_counter}/{self.game.max_iterations}] completed in {dt*1000.0:.4f}ms")
		
				sleep_time = tick_step - dt
				if sleep_time > 0:
					logger.debug(f"has time to sleep for {sleep_time}sec")
					time.sleep(sleep_time)

		except KeyboardInterrupt:
			logger.info(f"user interrupted the game")
			pass
