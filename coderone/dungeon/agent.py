from enum import Enum
from typing import Dict, List, Tuple, Union, NamedTuple, Any, Optional

Point = Tuple[int, int]
PID = int


class EntityTags(Enum):
	Ammo = "a"
	Treasure = 't'
	Bomb = "b"

	SoftBlock = 'sb'
	OreBlock = 'ob'
	IndestructibleBlock = 'ib'


class GameState:
	""" A state of the game as viewed by an agent.
	All agent receive the state game state each step to base their decisions on.
	"""

	def __init__(self, is_over:bool, tick_number:int, size:Point, 
				game_map:Dict,
				ammo:List[Point],
				treasure:List[Point],
				bombs:List[Point],
				blocks,
				players,
				):
		self.is_over = is_over
		self.tick_number = tick_number
		self._size = size
		self._game_map = game_map
		self._treasure = treasure
		self._ammo = ammo
		self._bombs = bombs
		self._blocks = blocks
		self._players = players


	@property
	def size(self) -> Point:
		"""Get the size of the map area as a 'Point' tuple
		"""
		return self._size

	@property
	def ammo(self) -> List[Point]:
		return self._ammo

	@property
	def treasure(self) -> List[Point]:
		return self._treasure
	
	@property
	def bombs(self) -> List[Point]:
		"""Get a list of bombs placed on the map.
		"""
		return self._bombs

	@property
	def all_blocks(self) -> List[Point]:
		return [pos for tag, pos in self._blocks]

	@property
	def indestructible_blocks(self) -> List[Point]:
		return [pos for tag, pos in self._blocks if tag == EntityTags.IndestructibleBlock.value]

	@property
	def soft_blocks(self) -> List[Point]:
		return [pos for tag, pos in self._blocks if tag == EntityTags.SoftBlock.value]
	
	@property
	def ore_blocks(self) -> List[Point]:
		return [pos for tag, pos in self._blocks if tag == EntityTags.OreBlock.value]

	def is_in_bounds(self, location:Point) -> bool:
		return 	location[0] >= 0 and location[0] < self.size[0] and \
				location[1] >= 0 and location[1] < self.size[1]

	def _has_occupancy(self, location:Point) -> bool:
		return location[0] in self._game_map and location[1] in self._game_map[location[0]]

	def entity_at(self, location:Point) -> EntityTags:
		if not self.is_in_bounds(location):
			return None

		return self._game_map[location[0]][location[1]] if self._has_occupancy(location) else None

	def is_occupied(self, location:Point) -> bool:
		return self.entity_at(location) is not None

	def opponents(self, excluding_player_pid:PID):
		return [pos for pid, pos in self._players if excluding_player_pid and pid != excluding_player_pid or not excluding_player_pid]


class PlayerState:
	def __init__(self, id:PID, ammo:int, hp:int, location:Point, reward:int, power:int):
		self.id = id
		self.ammo = ammo
		self.hp = hp
		self.location = location
		self.reward = reward
		self.power = power


class Agent:
	
	def next_move(self, game_state:GameState, player_state:PlayerState):
		pass
	
	def on_game_over(self, game_state:GameState, player_state:PlayerState):
		pass
