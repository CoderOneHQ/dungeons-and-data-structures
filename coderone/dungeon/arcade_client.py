import arcade
from pyglet.gl import GL_NEAREST

from .asset_manager import AssetManager, AssetType
from .game import PlayerActions, Point, PID, Game

# WIDTH and HEIGHT of each grid cell in pixels
WIDTH = 64
HEIGHT = 64
PADDING = (int(WIDTH/2), HEIGHT)


def grid_to_pos(pos:Point):
	x = PADDING[0] + pos[0] * WIDTH + (WIDTH / 2)
	y = PADDING[1] + pos[1] * HEIGHT  + (HEIGHT / 2)
	return x,y 


class Sfx(arcade.Sprite):
	""" Special visual effects
		animation with no game mechanics impact
	"""

	def __init__(self, loc:Point, texture_list):
		super().__init__()
		self.center_x,self.center_y = grid_to_pos(loc)

		# Start at the first frame
		self.current_texture = 0
		self.textures = texture_list
		self.set_texture(self.current_texture)

	def update(self):
		self.current_texture += 1
		if self.current_texture < len(self.textures):
			self.set_texture(self.current_texture)
		else:
			self.remove_from_sprite_lists()

class StaticSprite(arcade.Sprite):
	def __init__(self, asset, owner, scale):
		super().__init__(asset, scale)
		self.owner = owner
		x, y = grid_to_pos(self.owner.pos)
		self.set_position(x, y)

	def update_pos(self):
		x, y = grid_to_pos(self.owner.pos)
		self.set_position(x, y)

class Player(StaticSprite):
	""" Player Class """
	def __init__(self, asset, owner):
		super().__init__(asset, owner, scale=1.0)

	def update(self):
		""" Move the player """
		self.update_pos()
		if not self.owner.is_alive:
			self.remove_from_sprite_lists()


class Client(arcade.Window):
	"""
	Main application class.
	"""

	def _add_wall(self, col, row, asset):
		tile = arcade.Sprite(asset, 4)
		x,y = grid_to_pos((col,row))
		tile.set_position(x,y)
		self.chrome_tiles.append(tile)

	def __init__(self, width:int, height:int, title:str, game:Game, config, interactive:bool, user_pid:PID):
		"""
		Set up the application.
		"""
		super().__init__(width, height, title)

		self.app_config = config
		self.asset_man = AssetManager(config.get('assets'))
		self.game = game
		self.user_pid = user_pid
		self.interactive = interactive
		self.paused = self.app_config.get('start_paused', False)
		self.end_game_wait_time = self.app_config.get('wait_end', 10)
		self.end_game_timer = self.end_game_wait_time

		arcade.set_background_color(arcade.color.BLACK)


		# Pre-load the animation frames. We don't do this in the __init__
		# of the explosion sprite because it
		# takes too long and would cause the game to pause.
		columns = 16
		count = 60
		sprite_width = 256
		sprite_height = 256

		# Load the explosions from a sprite sheet
		self.explosion_texture_list = arcade.load_spritesheet(self.asset_man.explosion, sprite_width, sprite_height, columns, count)

		# Loading explostions sound
		self.hit_sound = arcade.sound.load_sound(self.asset_man.explosion_sound)

		self.chrome_tiles = arcade.SpriteList()
		self._add_wall(-1, self.game.row_count + 1, self.asset_man.asset("chrome/wall_side_top_left.png", AssetType.IMAGE))
		self._add_wall(self.game.column_count, self.game.row_count + 1, self.asset_man.asset("chrome/wall_side_top_right.png", AssetType.IMAGE))

		self._add_wall(-1, -1, self.asset_man.asset("chrome/wall_side_front_left.png", AssetType.IMAGE))
		self._add_wall(self.game.column_count, -1, self.asset_man.asset("chrome/wall_side_front_right.png", AssetType.IMAGE))
		
		self._add_wall(0, self.game.row_count, self.asset_man.asset("chrome/wall_corner_front_left.png", AssetType.IMAGE))
		self._add_wall(0, self.game.row_count + 1, self.asset_man.asset("chrome/wall_corner_top_left.png", AssetType.IMAGE))

		self._add_wall(self.game.column_count - 1, self.game.row_count, self.asset_man.asset("chrome/wall_corner_front_right.png", AssetType.IMAGE))
		self._add_wall(self.game.column_count - 1, self.game.row_count+1, self.asset_man.asset("chrome/wall_corner_top_right.png", AssetType.IMAGE))

		self._add_wall(0, 0, self.asset_man.asset("chrome/wall_top_left.png", AssetType.IMAGE))
		self._add_wall(self.game.column_count - 1, 0, self.asset_man.asset("chrome/wall_top_right.png", AssetType.IMAGE))
		for column in range(1, self.game.column_count - 1):
			self._add_wall(column, self.game.row_count+1, self.asset_man.asset("chrome/wall_top_mid.png", AssetType.IMAGE))
			self._add_wall(column, 0, self.asset_man.asset("chrome/wall_top_mid.png", AssetType.IMAGE))
			self._add_wall(column, self.game.row_count, self.asset_man.asset("chrome/wall_mid.png", AssetType.IMAGE))
			

		for column in range(0, self.game.column_count):
			self._add_wall(column, -1, self.asset_man.asset("chrome/wall_mid.png", AssetType.IMAGE))

		for row in range(0, self.game.row_count+1):
			self._add_wall(-1, row, self.asset_man.asset("chrome/wall_side_mid_left.png", AssetType.IMAGE))
			self._add_wall(self.game.column_count, row, self.asset_man.asset("chrome/wall_side_mid_right.png", AssetType.IMAGE))

		self._map_game()

	def _add_blocks(self, asset, blocks, scale=4):
		self.block_list.extend(map(lambda block: StaticSprite(asset, block, scale), blocks))

	def _map_game(self):
		self.player_list = arcade.SpriteList()
		self.grid_sprite_list = arcade.SpriteList()
		self.block_list = arcade.SpriteList()
		self.sfx_list = arcade.SpriteList()

		# Create a list of solid-color sprites to represent each grid location
		for column in range(self.game.column_count):
			for row in range(self.game.row_count):
				sprite = arcade.Sprite(self.asset_man.floor_tile, 4)
				x,y = grid_to_pos((column, row))
				sprite.set_position(x, y)
				self.grid_sprite_list.append(sprite)

		# Create player sprites
		self.player_list.extend([Player(self.asset_man.player_avatar(pid), player) for pid, player in self.game.players.items()])
		
		self._add_blocks(self.asset_man.indestructible_block, self.game.static_block_list)
		self.block_list.extend(map(lambda block: StaticSprite(self.asset_man.ore_block if block.hp > 1 else self.asset_man.soft_block, block, 4.0), self.game.value_block_list))

		self._add_blocks(self.asset_man.ammunition, self.game.ammunition_list, 1)
		self._add_blocks(self.asset_man.treasure, 	self.game.treasure_list, 1)
		self._add_blocks(self.asset_man.bomb, 		self.game.bomb_list, 1)
		self._add_blocks(self.asset_man.fire, 		self.game.fire_list)
		self._add_blocks(self.asset_man.skeleton, 	self.game.dead_player_list)

	def _update_map(self):
		# Remove all the blocks that are not in game
		to_remove = [sprite for sprite in self.block_list if sprite.owner not in self.game.all_entities]
		for sprite in to_remove:
			sprite.remove_from_sprite_lists()

		all_block_owner = [sprite.owner for sprite in self.block_list]
		self._add_blocks(self.asset_man.ammunition, [block for block in self.game.ammunition_list if block not in all_block_owner], 1)
		self._add_blocks(self.asset_man.treasure, 	[block for block in self.game.treasure_list if block not in all_block_owner], 1)
		self._add_blocks(self.asset_man.bomb, 		[block for block in self.game.bomb_list if block not in all_block_owner], 1)
		self._add_blocks(self.asset_man.fire, 		[block for block in self.game.fire_list if block not in all_block_owner])
		self._add_blocks(self.asset_man.skeleton, 	[block for block in self.game.dead_player_list if block not in all_block_owner])

		new_fire = [block for block in self.game.fire_list if block not in all_block_owner]
		self._add_blocks(self.asset_man.fire, 		new_fire)
		
		# Add Fire-SFX for each new fire position
		self.sfx_list.extend(map(lambda fire: Sfx(fire.pos, self.explosion_texture_list), new_fire))

	def tick_game(self, time_interval):
		if not self.paused: # if game has paused then stop
			self.game.tick(time_interval)

	def run(self, time_interval):
		# Enable fixed interval timer
		arcade.schedule(self.tick_game, time_interval)
		arcade.run()

	def on_draw(self):
		""" Render the screen """
		# This command has to happen before we start drawing
		arcade.start_render()

		self.grid_sprite_list.draw(filter=GL_NEAREST)
		self.block_list.draw(filter=GL_NEAREST)

		#drawing player
		self.player_list.draw(filter=GL_NEAREST)

		self.sfx_list.draw()

		self.chrome_tiles.draw(filter=GL_NEAREST)

		# Print scores on the screen
		d_height = 20
		current_text_height = self.height - d_height
		if not self.app_config.get('no_text', False):
			for pid, player in self.game.players.items():
				name = "{}{}".format(player.name, '(bot)' if self.game.is_bot(pid) else "")
				player_output = f"{name} HP: {player.hp:3d} / Ammo: {player.ammo:3d} / Score: {player.reward:4d}"

				arcade.draw_text(player_output, 10, current_text_height, arcade.color.WHITE, 14, font_name='arial')
				current_text_height -= d_height

		if self.paused and not self.app_config.get('no_text', False):
			arcade.draw_text("PAUSED", self.width / 2, self.height / 2, arcade.color.WHITE, 42, bold=True,
								font_name='arial',
								align="center", anchor_x="center", anchor_y="center")

		if self.game.is_over:
			progress = 360*(1 - self.end_game_timer / self.end_game_wait_time)
			sq_size = self.height / 4
			width = sq_size / 4
			arcade.draw_arc_outline(center_x=self.width / 2, center_y=self.height / 2, 
									width=sq_size, height=sq_size, color=arcade.color.CYAN,
									border_width=width,
									start_angle=0, end_angle=progress,
									tilt_angle=90)

			# if not self.app_config.get('no_text', False):
			# 	arcade.draw_text(f"GAME OVER\n{self.end_game_timer:2.1f}", 
			# 	self.width / 2, self.height / 2, arcade.color.BLACK, 42, bold=True,
			# 						font_name='arial',
			# 						align="center", anchor_x="center", anchor_y="center")

		#arcade.finish_render()

	def on_update(self, delta_time):
		""" Update game state """
		if self.paused: # if game has paused then don't update it
			return
		
		game_over = self.game.is_over
		if game_over:  # Game over count-down
			self.end_game_timer -= delta_time
		
		if self.end_game_timer < 0:
			self.close()
			return

		# Normal game update
		self.player_list.update()
		self.sfx_list.update()

		self._update_map()

	def on_key_press(self, key, modifiers):
		"""Called whenever a key is pressed. """

		if key == arcade.key.ENTER:
			self.paused = not self.paused

		if self.interactive and key == arcade.key.R:
			self.paused = True
			self.end_game_timer = self.end_game_wait_time
			self.game.generate_map()
			self._map_game()

		# Next command are only accepted if game is not paused:
		if self.paused or not self.interactive or not self.user_pid:
			return

		if key == arcade.key.UP or key == arcade.key.W:
			self.game.enqueue_action(self.user_pid, PlayerActions.MOVE_UP)
		elif key == arcade.key.DOWN or key == arcade.key.D:
			self.game.enqueue_action(self.user_pid, PlayerActions.MOVE_DOWN)
		elif key == arcade.key.LEFT or key == arcade.key.A:
			self.game.enqueue_action(self.user_pid, PlayerActions.MOVE_LEFT)
		elif key == arcade.key.RIGHT or key == arcade.key.D:
			self.game.enqueue_action(self.user_pid, PlayerActions.MOVE_RIGHT)
		elif key == arcade.key.SPACE:
			self.game.enqueue_action(self.user_pid, PlayerActions.PLACE_BOMB)
