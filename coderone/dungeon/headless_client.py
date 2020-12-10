import time
import logging


logger = logging.getLogger(__name__)

class Client:
	def __init__(self, game, config):
		self.game = game
		self.config = config

	def _update(self, tick_step):
		self.game.tick(tick_step)

		stats = self.game.stats
		for p in stats.players.values():
			name = "{}{}".format(p.name, '(bot)' if p.is_bot else "")
			logger.info(f"{name} HP: {p.hp} / Ammo: {p.ammo} / Score: {p.score}, loc: ({p.position[0]}, {p.position[1]})")

	def run(self, tick_step):
		try:
			while not self.game.is_over:
				logger.info(f"game-step [{self.game.tick_counter}/{self.game.max_iterations}]")
				
				cycle_start_time = time.time()
				self._update(tick_step)
				dt = time.time() - cycle_start_time
				logger.debug(f"game-step [{self.game.tick_counter}/{self.game.max_iterations}] completed in {dt*1000.0:.4f}ms")
		
				sleep_time = tick_step - dt
				if sleep_time > 0:
					logger.debug(f"has time to sleep for {sleep_time}sec")
					time.sleep(sleep_time)

		except KeyboardInterrupt:
			logger.info(f"user interrupted the game")
			pass
