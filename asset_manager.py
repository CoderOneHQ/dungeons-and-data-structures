from enum import Enum
import os
import random

ASSET_DIRECTORY = 'assets'


class AssetType(Enum):
	IMAGE = 'images'
	SOUND = 'sounds'

class AssetManager:

	# Images
	BOMB_IMAGE = "bomb_64px.png"
	AMMUNITION_IMAGE = "chest.png"
	CRATE_IMAGE = "crate.png"
	SKELETON_IMAGE = "skelet_run_anim_f1.png"
	FIRE_IMAGE = "coin_anim_f0.png"

	# Sounds
	EXP_SOUND = "explosion.mp3"

	FLOOR_TILES = ["floor_1.png", "floor_2.png", "floor_3.png", "floor_4.png", "floor_5.png", "floor_6.png", "floor_7.png", "floor_8.png"]
	PLAYER_AVATARS = [
		"p1_knight_64px.png",
		"p2_knight_64px.png",
		"p2_knight_64px_flipped.png", 
		"p2_knight_orange_64px_flipped.png", 
		]
	
	def __init__(self, asset_dir:str=ASSET_DIRECTORY):
		self.asset_dir = asset_dir

	@property
	def floor_tile(self):
		tile = random.choice(self.FLOOR_TILES)
		return self.asset(tile, AssetType.IMAGE)

	@property
	def metal_block(self):
		SOFT_METAL_BLOCK_IMAGE = "soft_block_transparent_metal.png"
		return self.asset(SOFT_METAL_BLOCK_IMAGE, AssetType.IMAGE)

	@property
	def crate(self):
		return self.asset(self.CRATE_IMAGE, AssetType.IMAGE)

	@property
	def bomb(self):
		return self.asset(self.BOMB_IMAGE, AssetType.IMAGE)

	@property
	def ammunition(self):
		return self.asset(self.AMMUNITION_IMAGE, AssetType.IMAGE)

	@property
	def skeleton(self):
		return self.asset(self.SKELETON_IMAGE, AssetType.IMAGE)

	@property
	def fire(self):
		return self.asset(self.FIRE_IMAGE, AssetType.IMAGE)

	@property
	def explosion_sound(self):
		return self.asset(self.EXP_SOUND, AssetType.SOUND)

	def player_avatar(self, pid):
		avatar = self.PLAYER_AVATARS[pid % len(self.PLAYER_AVATARS)]
		return self.asset(avatar, AssetType.IMAGE)

	def asset(self, name, assetType: AssetType):
		return os.path.join(self.asset_dir, assetType.value, name)
