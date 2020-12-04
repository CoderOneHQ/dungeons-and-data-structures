import random
import logging

from enum import Enum
from typing import Dict, List, Tuple, Union, NamedTuple, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Typings
Point = Tuple[int, int]
PID = int


class DelayedEffectType(Enum):
	SPAWN_AMMO = 'a'

class PlayerActions(Enum):
	NO_OP = ''
	MOVE_UP = 'u'
	MOVE_DOWN = 'd'
	MOVE_LEFT = 'l'
	MOVE_RIGHT = 'r'
	PLACE_BOMB = 'b'

class GameSysActions(Enum):
	MAP = "map" 					# A new map generated
	PLAYER_ADDED = "add_player" 	# Add a new player to the game

class GameSysAction(NamedTuple):
	action: GameSysActions
	payload: Any

class PlayerMove(NamedTuple):
	pid: PID
	action: PlayerActions

GameEvent = Union[GameSysActions, PlayerMove]


def collide(pos1:Point, pos2:Point) -> bool: 
	return (pos1[0] == pos2[0]) and (pos1[1] == pos2[1])


class Recorder:
	def record(self, tick:int, event:GameEvent):
		pass
	
	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		pass

class Game:
	"""Game class defining game rules
	"""
	# Set how many rows and columns we will have
	ROW_COUNT = 10
	COLUMN_COUNT = 12

	SOFTBLOCK_COUNT = 30
	HARDBLOCK_COUNT = 10
	PLAYER_START_AMMO = 3
	FREE_AMMO_COUNT = 1

	# Rewards
	FIRE_PENALTY = 25
	FIRE_REWARD = 25
	SOFTBLOCK_REWARD = 2
	HARDBLOCK_REWARD = 5

	PLAYER_START_HP = 2 # Initial hp of a new player
	SOFTBLOCK_HP = 1 # Initial hp of a soft block
	METALBLOCK_HP = 4 # Initial hp of a metal block

	FIRE_HIT = 1 # Number of hit points taken by the fire

	PLAYER_START_POWER = 2 # Initial blast radius
	BOMB_TTL = 35 # Number of turns before bomb expires
	AMMO_RESPAWN_TTL = 2*BOMB_TTL # Number of turns before ammo respawns
	

	ACTION_CODES = {
		'u': PlayerActions.MOVE_UP,
		'd': PlayerActions.MOVE_DOWN,
		'l': PlayerActions.MOVE_LEFT,
		'r': PlayerActions.MOVE_RIGHT,
		'p': PlayerActions.PLACE_BOMB,
		}

	class _Positioned:
		def __init__(self, pos: Point):
			self.pos = pos

	class _Destructable(_Positioned):
		def __init__(self, ttl:int, pos: Point):
			super().__init__(pos)
			self._ttl = ttl

		@property
		def is_alive(self):
			return self._ttl > 0

		@property
		def hp(self):
			return self._ttl

		def apply_hit(self, delta_ttl:int) -> int:
			self._ttl -= delta_ttl
			return self._ttl

		def update(self) -> int:
			return self._ttl

	class _Perishable(_Destructable):
		def update(self) -> int:
			return self.apply_hit(1)

	class _DelayedEffect(_Perishable):
		def __init__(self, effect: DelayedEffectType, ttl:int):
			super().__init__(ttl=ttl, pos=None)
			self.effect = effect

	class _OwnedPositionedPerishable(_Perishable):
		def __init__(self, owner_id, pos: Point, ttl:int=1):
			super().__init__(pos=pos, ttl=ttl)
			self.owner_id = owner_id

	class _DeadBody(_Positioned):
		def __init__(self, pid, pos: Point):
			super().__init__(pos=pos)
			self.pid = pid

	class _Player(_Destructable):
		def __init__(self, hp:int, pos:Point, ammo:int, name:str, power:int, reward:int=0):
			super().__init__(pos=pos, ttl=hp)
			self.name = name
			self.ammo = ammo
			self.reward = reward
			self.power = power
			

	class _Ammunitation(_Positioned):
		Tag = "a"

		def __init__(self, pos: Point, value: int=1):
			super(Game._Ammunitation, self).__init__(pos=pos)
			self.value = value

		@property
		def is_alive(self):
			return self.value > 0

		def update(self):
			pass

	class _Bomb(_OwnedPositionedPerishable):
		Tag = "b"

		def __init__(self, owner_id:PID, pos:Point, ttl:int, power:int):
			super().__init__(owner_id=owner_id, pos=pos, ttl=ttl)
			self.power = power

	class _Fire(_OwnedPositionedPerishable):
		pass

	class _SoftBlock(_Destructable):
		Tag = 'sb'

		def __init__(self, pos:Point, hp:int):
			super().__init__(pos=pos, ttl=hp)
			self.reward = Game.SOFTBLOCK_REWARD

	class _MetalBlock(_Destructable):
		Tag = 'mb'

		def __init__(self, pos:Point, hp:int):
			super().__init__(pos=pos, ttl=hp)
			self.reward = Game.HARDBLOCK_REWARD


	def __init__(self, row_count=ROW_COUNT, column_count=COLUMN_COUNT, max_iterations=None, recorder=Recorder()):
		self.game_ended = False
		self.row_count = row_count
		self.column_count = column_count
		self.recorder = recorder

		self.ACTION_CODES.setdefault(None)

		self.tick_counter = 0
		self.max_iterations = max_iterations
		self._pid_counter = 0
		self._agents = {}

		self.players:Dict[PID, self._Player] = {}
		
		self._reset_state()

	def is_bot(self, pid:int) -> bool:
		return pid in self._agents

	def _player_stat(self, pid, player):
		return {
			'name':  player.name,
			'is_bot': self.is_bot(pid),
			'score': player.reward,
			'hp': player.hp,
			'ammo': player.ammo,
			'position': player.pos
		}

	def stats(self):
		return {
			'game_over': self.game_ended,
			'iteration': self.tick_counter,
			'players': { k: self._player_stat(k, p) for k, p in self.players.items() }
		}

	def _reset_state(self):
		# Recet actions queues
		self._action_queue:Dict[PID, List[PlayerActions]] = defaultdict(lambda: [])
		self._delayed_effects:List[Game._DelayedEffect] = []

		self.ammunition_list:List[Game._Ammunitation] = []
		self.bomb_list:List[Game._Bomb] = []
		self.fire_list:List[Game._Fire] = []
		self.block_list:List[Game._Destructable] = []
		self.dead_player_list:List[Game._DeadBody] = []

		for player in self.players.values():
			player.ammo = self.PLAYER_START_AMMO
			player.reward = 0

		self.all_entities = []

	def generate_map(self, seed=1):
		self._reset_state()

		all_cells = []
		for x in range(0, self.column_count):
			for y in range(0, self.row_count):
				all_cells.append((x,y))

		# Place players
		for player in self.players.values():
			player.pos = random.choice(all_cells)
			all_cells.remove(player.pos)
			# Make sure there are at least 5 free cells around a player spawning position
			x, y = player.pos
			cross =  [ (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1) ]
			extras = [ (x - 2, y), (x + 2, y), (x, y - 2), (x, y + 2) ]
			for c in cross:
				if c in all_cells:
					all_cells.remove(c)
			while extras:
				e_id = random.choice(range(0, len(extras)))
				e = extras.pop(e_id)
				if e in all_cells:
					all_cells.remove(e)
					break

		soft_blocks = random.sample(all_cells, self.SOFTBLOCK_COUNT)
		for cell in soft_blocks:
			self.block_list.append(self._SoftBlock(cell, self.SOFTBLOCK_HP))
			all_cells.remove(cell)

		metal_blocks = random.sample(all_cells, self.HARDBLOCK_COUNT)
		for cell in metal_blocks:
			self.block_list.append(self._MetalBlock(cell, self.METALBLOCK_HP))
			all_cells.remove(cell)

		free_ammo = random.sample(all_cells, self.FREE_AMMO_COUNT)
		for cell in free_ammo:
			self.ammunition_list.append(self._Ammunitation(cell))
			all_cells.remove(cell)

		self.all_entities = self.bomb_list + self.fire_list + self.ammunition_list + self.block_list
		self.recorder.record(self.tick_counter, GameSysAction(GameSysActions.MAP, self._serialize_map()))


	def _serialize_map(self):
		# Create an occupancy map for AI-agents to base decisions on
		game_map ={}

		def __set_tag(pos, tag):
			game_map.setdefault(pos[0], {})
			game_map[pos[0]][pos[1]] = tag

		# updating the ascii map with players
		for pid, player in self.players.items():
			__set_tag(player.pos, pid)

		for item in self.block_list:
			__set_tag(item.pos, item.Tag)

		for item in self.ammunition_list:
			__set_tag(item.pos, item.Tag)

		for item in self.bomb_list:
			__set_tag(item.pos, item.Tag)

		return game_map		

	def _is_in_bounds(self, p:Point):
		return  p[0] >= 0 and p[0] < self.column_count and \
				p[1] >= 0 and p[1] < self.row_count

	def _collision_list(self, pos, items_list):
		return [p for p in items_list if collide(pos, p.pos)]

	def _next_pid(self) -> PID:
		pid, self._pid_counter = self._pid_counter, self._pid_counter + 1
		return pid

	def _enqueue_effect(self, effect: _DelayedEffect):
		if not effect:
			return

		self._delayed_effects.append(effect)


	def enqueue_action(self, pid:PID, action: PlayerActions):
		""" Add action to the queue of player actions
		"""
		if not action:
			return

		self._action_queue[pid].append(action)

	def _apply_action(self, pid: PID, action: PlayerActions) -> bool:
		self.recorder.record(self.tick_counter, PlayerMove(pid=pid, action=action))

		if not action:
			return False

		player = self.players[pid] if pid in self.players else None
		if not player or not player.is_alive: # Dead or non-existing players can't move, obsly
			return False

		if   action == PlayerActions.NO_OP:			return True
		elif action == PlayerActions.MOVE_UP: 		return self._move(pid, player, (0, +1))
		elif action == PlayerActions.MOVE_DOWN: 	return self._move(pid, player, (0, -1))
		elif action == PlayerActions.MOVE_LEFT: 	return self._move(pid, player, (-1, 0))
		elif action == PlayerActions.MOVE_RIGHT:	return self._move(pid, player, (+1, 0))
		elif action == PlayerActions.PLACE_BOMB:	return self._place_bomb(pid, player)
		else:
			logger.error(f"Attempt to apply unknown action: '{action}'")
			# TODO: Record cheeting attempt
			return False

	def _apply_effect(self, effect: DelayedEffectType):
		if not effect: return

		if effect == DelayedEffectType.SPAWN_AMMO: self._spawn_ammo()
		else:
			logger.error(f"Attempt to apply unknown effect: '{effect}'")
			# TODO: Record cheeting attempt

	def __update_list(self, lt):
		for i in lt:
			i.update()

	def _only_alive(self, items):
		return [i for i in items if i.is_alive]

	def _alive_players(self):
		return [(pid,p) for pid,p in self.players.items() if p.is_alive]

	def tick(self, dt:float):
		if not self.game_ended:
			self.tick_counter += 1
			
			game_map = self._serialize_map()
			state = self._current_state()

			# Gather agents commands
			for pid, agent in self._agents.items():
				self._update_agent(dt, pid, agent, game_map, state)

			# Apply enqueued actions
			orders_for_tick = []
			for pid, action_queue in self._action_queue.items():
				if action_queue:
					action = action_queue.pop(0)
					orders_for_tick.append((pid, action))
			
			# Randomize the order of actions?
			random.shuffle(orders_for_tick)
			for pid, action_queue in orders_for_tick:
				self._apply_action(pid, action)

		# Apply fire!
		for pid, player in self._alive_players():
			hit_list = self._collision_list(player.pos, self.fire_list)
			for hit in hit_list:
				fire_owner = self.players[hit.owner_id] if hit.owner_id in self.players else None

				# Apply fire damage to the player
				player.apply_hit(self.FIRE_HIT)

				player.reward -= self.FIRE_PENALTY
				if player != fire_owner and fire_owner:
					fire_owner.reward += self.FIRE_REWARD


		for fire in self.fire_list:
			fire_owner = self.players[fire.owner_id] if fire.owner_id in self.players else None
			
			hitblock_list = self._collision_list(fire.pos, self.block_list)
			for block in hitblock_list:
				block.apply_hit(self.FIRE_HIT)
				if not block.is_alive and fire_owner:
					fire_owner.reward += block.reward
			
			hitbomb_list = self._collision_list(fire.pos, self.bomb_list)
			for bomb in hitbomb_list:
				bomb.apply_hit(bomb.hp)

		# Pickup ammo:
		for pid, player in self._alive_players():
			if player.is_alive: # Dead players are not allowed to pickup items
				ammo_found = self._collision_list(player.pos, self.ammunition_list)
				for am in ammo_found:
					player.ammo += am.value
					am.value = 0

		# Update effects and lists
		self.__update_list(self._delayed_effects)
		self.__update_list(self.bomb_list)
		self.__update_list(self.fire_list)
		self.__update_list(self.ammunition_list)
		self.__update_list(self.block_list)
		self.__update_list(self.players.values())
		
		# Turn not alive player into dead bodies:
		for pid, player in self.players.items():
			if not player.is_alive:
				self.dead_player_list.append(self._DeadBody(pid, player.pos))

		# Convert expired bomb into fire
		for p in self.bomb_list:
			if not p.is_alive: # Start a fire
				self._start_fire(p.owner_id, p.pos, p.power)

		# Apply delayed effects
		for p in self._delayed_effects:
			if not p.is_alive: # Apply delayed effect
				self._apply_effect(p.effect)

		# Remove expired entiries
		self._delayed_effects = self._only_alive(self._delayed_effects)

		self.bomb_list = 		self._only_alive(self.bomb_list)
		self.fire_list =		self._only_alive(self.fire_list)
		self.ammunition_list =	self._only_alive(self.ammunition_list)
		self.block_list =		self._only_alive(self.block_list)
		#self.players = dict(filter(lambda p: p.is_alive, self.players.values()))

		# Combine all alive entities into a single list for quereing by the render engine
		self.all_entities = self.bomb_list + self.fire_list + self.ammunition_list + self.block_list

		# Evaluate game termination rule
		over_iter_limit = True if self.max_iterations and self.tick_counter > self.max_iterations else False
		has_opponents = sum(p.is_alive for p in self.players.values()) > 1
		self.game_ended = not has_opponents or over_iter_limit # There can be only one! 

	def add_agent(self, agent, name: Optional[str]) -> PID:
		pid = self.add_player(name)

		self._agents[pid] = agent

		return pid

	def add_player(self, name: Optional[str]) -> PID:
		player_id = self._next_pid()
		name = name or f"P[{player_id}]"
		self.players[player_id] = self._Player(hp=self.PLAYER_START_HP, pos=None, ammo=self.PLAYER_START_AMMO, name=name, power=self.PLAYER_START_POWER)

		self.recorder.record(self.tick_counter, GameSysAction(GameSysActions.PLAYER_ADDED, name))

		return player_id

	def _update_agent(self, delta_time: float, pid, agent, game_map, state):
		player = self.players[pid] if pid in self.players else None
		if not player or not player.is_alive:
			return
		
		logger.debug(f"[{player.name}] agent move....")
		chosen_move = agent.next_move(game_map, state)
		logger.debug(f"[{player.name}] agent move -> [{chosen_move}]")

		action = self.ACTION_CODES[chosen_move] if chosen_move in self.ACTION_CODES else None
		if action: 
			self.enqueue_action(pid, action)

	def _current_state(self):
		"""  
		Returns the current state of the game in a dictionary format
		for the developer to understand more of the world before making
		decision.
		"""
		state_dic = {
			'player_list': self.players
		}

		return state_dic

	def _try_add_fire(self, owner_pid:PID, pos:Point) -> bool:
		if not self._is_in_bounds(pos):
			return False
		
		if self._collision_list(pos, self.block_list) or self._collision_list(pos, self.bomb_list):
			self.fire_list.append(self._Fire(owner_pid, pos))
			return False

		self.fire_list.append(self._Fire(owner_pid, pos))
		return True

	def _start_fire(self, owner_pid:PID, loc:Point, power:int):
		(cell_x, cell_y) = loc

		self.fire_list.append(self._Fire(owner_pid, loc))
		for i in range(1, power + 1):
			if not self._try_add_fire(owner_pid, (cell_x - i, cell_y)): 
				break

		for i in range(1, power + 1):
			if not self._try_add_fire(owner_pid, (cell_x + i, cell_y)):
				break

		for i in range(1, power + 1):
			if not self._try_add_fire(owner_pid, (cell_x, cell_y - i)):
				break
		
		for i in range(1, power + 1):
			if not self._try_add_fire(owner_pid, (cell_x, cell_y + i)):
				break

	def _place_bomb(self, pid: PID, player: _Player) -> bool:
		if player.ammo <= 0: # Need to have something to place
			return False
		
		player.ammo -= 1

		self.bomb_list.append(self._Bomb(pid, player.pos, self.BOMB_TTL, player.power))
		# TODO Update occupancy greed

		# Schedule respawn of an ammo for the next turn
		self._enqueue_effect(self._DelayedEffect(effect=DelayedEffectType.SPAWN_AMMO, ttl=self.AMMO_RESPAWN_TTL))

		return True

	def _move(self, pid: PID, player: _Player, delta) -> bool:
		new_loc = (max(0, min(player.pos[0] + delta[0], self.column_count - 1)), max(0, min(player.pos[1] + delta[1], self.row_count-1)))
		if self._has_collision(new_loc):
			return False

		player.pos = new_loc
		
		return True

	def _spawn_ammo(self):
		all_cells = []

		def __safe_remove(pos):
			try:
				all_cells.remove(pos)
			except:
				pass

		for x in range(0, self.column_count):
			for y in range(0, self.row_count):
				all_cells.append((x,y))

		# Don't spawn ammo on top of a player
		for player in self.players.values():
			__safe_remove(player.pos)

		# Don't spawn ammo on top of a block
		for block in self.block_list:
			__safe_remove(block.pos)

		# Don't spawn ammo on top of another ammo
		for ammo in self.ammunition_list:
			__safe_remove(ammo.pos)

		# Don't spawn ammo on top of a bomb
		for ammo in self.bomb_list:
			__safe_remove(ammo.pos)

		loc = random.choice(all_cells)
		self.ammunition_list.append(Game._Ammunitation(loc))


	def _has_collision(self, pos:Point) -> bool:
		""" It checks if a player can move to a new location"""
		# Check if given postion overlaps with any of the blocks
		hit_list = self._collision_list(pos, self.block_list)

		# Check if given postion overlaps with any of the players
		# This makes players non-clipable
		hit_list += self._collision_list(pos, self.players.values())

		# Loop through each colliding sprite, remove it, and add to the score.
		return len(hit_list) > 0

