import random
import logging

from enum import Enum
from typing import Dict, List, Tuple, Union, NamedTuple, Any, Optional
# from dataclasses import dataclass
from collections import defaultdict

from .agent import Agent, Point, PID, EntityTags, GameState, PlayerState

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class DelayedEffectType(Enum):
	SPAWN_AMMO = 'a'
	SPAWN_TREASURE = 't'

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


# @dataclass
class PlayerStat(NamedTuple):
	name: str
	is_bot: bool
	score: int
	hp: int
	ammo: int
	position: Point

# @dataclass
class GameStats(NamedTuple):
	is_over: bool
	iteration:int
	winner_pid: PID
	players: Dict[PID, PlayerStat]


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

	# We have total 12x10 = 120 cells
	STATIC_BLOCK_COUNT = 18 	# 15% of the board are Indestructible blocks
	SOFT_BLOCK_COUNT = 20		# 20% of the board are low-value destructable blocks
	ORE_BLOCK_COUNT = 5			# 5% of the board are Ore blocks

	PLAYER_START_AMMO = 3		# Amount of ammo a player starts the match with
	FREE_AMMO_COUNT = 1			# Amount of free ammo, Should be Number of players - 1 - to create resource scarcity

	# Rewards and punishment
	FIRE_PENALTY = 0
	FIRE_REWARD = 25
	
	TREASURE_REWARD = 1
	SOFT_BLOCK_REWARD = 2
	ORE_BLOCK_REWARD = 10

	PLAYER_START_HP = 3 # Initial hp of a new player
	SOFTBLOCK_HP = 1	# Initial hp of a soft block
	ORE_BLOCK_HP = 3	# Initial hp of a ore block

	FIRE_HIT = 1 # Number of hit points taken by the fire

	PLAYER_START_POWER = 2 # Initial blast radius
	BOMB_TTL = 35 # Number of turns before bomb expires

	AMMO_PERISH_TTL = 5*BOMB_TTL # Number of turns before ammo expires
	AMMO_RESPAWN_TTL = 2*BOMB_TTL # Number of turns before ammo respawns
	TREASURE_SPAWN_FREQUENCY_MIN = 5*10 	# Once every 180 steps
	TREASURE_SPAWN_FREQUENCY_MAX = 25*10 	# Once every 180 steps
	

	ACTION_CODES = {
		'u': PlayerActions.MOVE_UP,
		'd': PlayerActions.MOVE_DOWN,
		'l': PlayerActions.MOVE_LEFT,
		'r': PlayerActions.MOVE_RIGHT,
		'p': PlayerActions.PLACE_BOMB,
		'b': PlayerActions.PLACE_BOMB,
		'can_haz_boom': PlayerActions.PLACE_BOMB,
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
			

	class _Ammunitation(_Perishable):
		Tag = EntityTags.Ammo.value

		def __init__(self, pos: Point, ttl: int, value: int=1, on_perish=None):
			super().__init__(pos=pos, ttl=ttl)
			self.value = value
			self.on_perish = on_perish

		@property
		def is_alive(self):
			return super().is_alive and self.value > 0

		def update(self):
			super().update()
			if not self.hp and self.on_perish:
				self.on_perish()


	class _Treasure(_Destructable):
		Tag = EntityTags.Treasure.value

		def __init__(self, pos: Point, value: int=None, ttl=1):
			super().__init__(pos=pos, ttl=1)
			self.value = value or Game.TREASURE_REWARD

		@property
		def is_alive(self):
			return super().is_alive and self.value > 0

		def update(self):
			pass


	class _Bomb(_OwnedPositionedPerishable):
		Tag = EntityTags.Bomb.value

		def __init__(self, owner_id:PID, pos:Point, ttl:int, power:int):
			super().__init__(owner_id=owner_id, pos=pos, ttl=ttl)
			self.power = power

	class _Fire(_OwnedPositionedPerishable):
		pass

	class _IndestructibleBlock(_Positioned):
		Tag = EntityTags.IndestructibleBlock.value

	class _SoftBlock(_Destructable):
		Tag = EntityTags.SoftBlock.value

		def __init__(self, pos:Point, hp:int):
			super().__init__(pos=pos, ttl=hp)
			self.reward = Game.SOFT_BLOCK_REWARD

	class _OreBlock(_Destructable):
		Tag = EntityTags.OreBlock.value

		def __init__(self, pos:Point, hp:int):
			super().__init__(pos=pos, ttl=hp)
			self.reward = Game.ORE_BLOCK_REWARD


	def __init__(self, row_count=ROW_COUNT, column_count=COLUMN_COUNT, max_iterations=None, recorder=Recorder()):
		self.row_count = row_count
		self.column_count = column_count
		self.recorder = recorder

		self.ACTION_CODES.setdefault(None)

		self.max_iterations = max_iterations
		self._pid_counter = 0
		self._agents:Dict[PID, Agent] = {}

		self.players:Dict[PID, self._Player] = {}
		
		self._reset_state()


	def add_agent(self, agent:Agent, name: Optional[str]) -> PID:
		""" Add new agent and a corresponding player to play the game
		"""
		pid = self.add_player(name)

		self._agents[pid] = agent

		return pid

	def add_player(self, name: Optional[str]) -> PID:
		""" Add a new player to play the game
		"""
		player_id = self._next_pid()
		name = name or f"P[{player_id}]"
		self.players[player_id] = self._Player(hp=self.PLAYER_START_HP, pos=None, ammo=self.PLAYER_START_AMMO, name=name, power=self.PLAYER_START_POWER)

		self.recorder.record(self.tick_counter, GameSysAction(GameSysActions.PLAYER_ADDED, name))

		return player_id

	def is_bot(self, pid:int) -> bool:
		""" Test if a give player_id belongs to the bot or a human player
		"""
		return pid in self._agents


	def enqueue_action(self, pid:PID, action: PlayerActions):
		""" Add an action to the queue of player's actions to be executed during next game tick
		"""
		if not action:
			return

		self._action_queue[pid].append(action)


	def tick(self, dt:float):
		""" Advance the state of the game by one step, which is dt sec in time.
		First, all agents are queried for their inputs based on the serialized state of the game.
		Then all enqueed player actions are applied first and object positions are updated accordingly.

		"""
		if not self.is_over:
			# Gather commands from agents
			for pid, agent in self._agents.items():
				action = self._get_agent_input(pid, agent)
				if action: 
					self.enqueue_action(pid, action)

			# Collect 1 enqueued action from each player for execution
			orders_for_tick = []
			for pid, action_queue in self._action_queue.items():
				if action_queue:
					action = action_queue.pop(0)
					orders_for_tick.append((pid, action))
			
			# Randomize the order in which actions appied.
			# This compemsates for low resolution of 100ms where informaion about exact timing of commands is lost.
			random.shuffle(orders_for_tick)
			for pid, action in orders_for_tick:
				self._apply_action(pid, action)

			# Apply fire!
			## Check if any player stepped into a fire-zone
			for pid, player in self._alive_players():
				hit_list = self._collision_list(player.pos, self.fire_list)
				for hit in hit_list:
					fire_owner = self.players[hit.owner_id] if hit.owner_id in self.players else None

					# Apply fire damage to the player
					player.apply_hit(self.FIRE_HIT)

					player.reward -= self.FIRE_PENALTY
					if player != fire_owner and fire_owner:
						fire_owner.reward += self.FIRE_REWARD


			## Apply fire damage to static entities
			for fire in self.fire_list:
				fire_owner = self.players[fire.owner_id] if fire.owner_id in self.players else None
				
				## Check for fire damage of static blocks and collect rewads
				hitblock_list = self._collision_list(fire.pos, self.value_block_list)
				for block in hitblock_list:
					block.apply_hit(self.FIRE_HIT)
					if not block.is_alive and fire_owner:
						fire_owner.reward += block.reward
				
				## Check for fire damage of nearby bombs and set them off
				hitbomb_list = self._collision_list(fire.pos, self.bomb_list)
				for bomb in hitbomb_list:
					bomb.apply_hit(bomb.hp)

			# Alive players get to pickup static rewards:
			for pid, player in self._alive_players():
				if player.is_alive: # Dead players are not allowed to pickup items
					# Pickup ammo:
					ammo_found = self._collision_list(player.pos, self.ammunition_list)
					for am in ammo_found:
						player.ammo += am.value
						am.value = 0

					# Pickup treasures:
					treasure_found = self._collision_list(player.pos, self.treasure_list)
					for treasure in treasure_found:
						player.reward += treasure.value
						treasure.value = 0

		# Update effects and lists
		self.__update_list(self._delayed_effects)
		self.__update_list(self.bomb_list)
		self.__update_list(self.fire_list)
		self.__update_list(self.ammunition_list)
		self.__update_list(self.value_block_list)
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

		self.ammunition_list =	self._only_alive(self.ammunition_list)
		self.treasure_list = 	self._only_alive(self.treasure_list)
		self.bomb_list = 		self._only_alive(self.bomb_list)
		self.fire_list =		self._only_alive(self.fire_list)
		self.value_block_list =	self._only_alive(self.value_block_list)
		#self.players = dict(filter(lambda p: p.is_alive, self.players.values()))

		# Evaluate game termination rules
		if not self.is_over:
			over_iter_limit = True if self.max_iterations and self.tick_counter > self.max_iterations else False
			has_opponents = sum(p.is_alive for p in self.players.values()) > 1

			# Game is over when there is at most 1 player left or 
			# Time limit (number of iterations) exceeded
			self.is_over = not has_opponents or over_iter_limit # There can be only one!

			if self.is_over:
				# Picking winners: last player standing or highest scoring corps
				self.winner = 	sorted(self.players.items(), key=lambda item: item[1].reward)[-1] if has_opponents else \
								next(((pid,p) for pid,p in self.players.items() if p.is_alive), None)

			game_state = self._serialize_state()
			
			# Update agents view of the world
			for pid, agent in self._agents.items():
				self._update_agent(dt, pid, agent, game_state)

		self.tick_counter += 1


	def _player_stat(self, pid, player) -> PlayerStat:
		return PlayerStat(
			name=player.name,
			is_bot=self.is_bot(pid),
			score=player.reward,
			hp=player.hp,
			ammo=player.ammo,
			position=player.pos
		)

	@property
	def stats(self) -> GameStats:
		return GameStats(
			is_over=self.is_over,
			iteration=self.tick_counter, 
			winner_pid=self.winner[0] if self.winner else None,
			players={ k: self._player_stat(k, p) for k, p in self.players.items()}
		)


	@property
	def all_blocks(self):
		return self.static_block_list + self.value_block_list

	@property
	def all_entities(self):
		# Combine all alive entities into a single list for quereing by the render engine
		return \
			self.static_block_list + \
			self.ammunition_list + \
			self.treasure_list + \
			self.bomb_list + \
			self.fire_list + \
			self.value_block_list


	def _reset_state(self):
		self.is_over = False
		self.winner = None
		self.tick_counter = 0

		# Recet actions queues
		self._action_queue:Dict[PID, List[PlayerActions]] = defaultdict(lambda: [])
		self._delayed_effects:List[Game._DelayedEffect] = []

		self.static_block_list:List[Game._IndestructibleBlock] = []

		self.ammunition_list:List[Game._Ammunitation] = []
		self.treasure_list:List[Game._Treasure] = []
		self.bomb_list:List[Game._Bomb] = []
		self.fire_list:List[Game._Fire] = []
		self.value_block_list:List[Game._Destructable] = []
		self.dead_player_list:List[Game._DeadBody] = []

		for player in self.players.values():
			player.ammo = self.PLAYER_START_AMMO
			player.power = self.PLAYER_START_POWER
			player.reward = 0
			player._ttl = self.PLAYER_START_HP


	def generate_map(self, seed=1):
		self._reset_state()

		# FIXME: We need to record enqueued delayed effects, otherwise replay won't match
		self._enqueue_effect(DelayedEffectType.SPAWN_TREASURE, ttl=random.randint(self.TREASURE_SPAWN_FREQUENCY_MIN, self.TREASURE_SPAWN_FREQUENCY_MAX))

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

		static_blocks = random.sample(all_cells, self.STATIC_BLOCK_COUNT)
		for cell in static_blocks:
			self.static_block_list.append(self._IndestructibleBlock(cell))
			all_cells.remove(cell)

		soft_blocks = random.sample(all_cells, self.SOFT_BLOCK_COUNT)
		for cell in soft_blocks:
			self.value_block_list.append(self._SoftBlock(cell, self.SOFTBLOCK_HP))
			all_cells.remove(cell)

		ore_blocks = random.sample(all_cells, self.ORE_BLOCK_COUNT)
		for cell in ore_blocks:
			self.value_block_list.append(self._OreBlock(cell, self.ORE_BLOCK_HP))
			all_cells.remove(cell)

		free_ammo = random.sample(all_cells, self.FREE_AMMO_COUNT)
		for cell in free_ammo:
			self.ammunition_list.append(self._Ammunitation(cell, ttl=self.AMMO_PERISH_TTL, on_perish=lambda: self._enqueue_effect(DelayedEffectType.SPAWN_AMMO, ttl=self.AMMO_RESPAWN_TTL)))
			all_cells.remove(cell)

		self.recorder.record(self.tick_counter, GameSysAction(GameSysActions.MAP, self._serialize_map()))

	def _serialize_state(self) -> GameState:
		return GameState(
				is_over=self.is_over,
				tick_number=self.tick_counter,
				size=(self.column_count, self.row_count),
				
				game_map=self._serialize_map(),
				ammo=[a.pos for a in self.ammunition_list].copy(),
				treasure=[a.pos for a in self.treasure_list].copy(),
				bombs=[a.pos for a in self.bomb_list].copy(),
				blocks=[(block.Tag, block.pos) for block in self.all_blocks].copy(),
				players=[(pid, player.pos) for pid, player in self.players.items()].copy(),
			)

	def _serialize_map(self):
		# Build an occupancy map for AI-agents to base decisions on
		game_map ={}

		def __set_tag(pos, tag):
			game_map.setdefault(pos[0], {})
			game_map[pos[0]][pos[1]] = tag

		for pid, player in self.players.items():
			__set_tag(player.pos, pid)

		for item in self.static_block_list:
			__set_tag(item.pos, item.Tag)

		for item in self.value_block_list:
			__set_tag(item.pos, item.Tag)

		for item in self.ammunition_list:
			__set_tag(item.pos, item.Tag)

		for item in self.treasure_list:
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

	def _enqueue_effect(self, effect: DelayedEffectType, ttl:int):
		if not effect or ttl <= 0:
			return

		self._delayed_effects.append(self._DelayedEffect(effect=effect, ttl=ttl))


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

		if 	effect == DelayedEffectType.SPAWN_AMMO: self._spawn_ammo()
		elif effect == DelayedEffectType.SPAWN_TREASURE: self._spawn_treasure()
		else:
			logger.error(f"Attempt to apply unknown effect: '{effect}'")
			# TODO: Record cheeting attempt

	def __update_list(self, lt):
		for i in lt:
			i.update()

	def _only_alive(self, items):
		return [i for i in items if i.is_alive]

	def _alive_players(self) -> List[Tuple[PID, _Player]]:
		return [(pid,p) for pid,p in self.players.items() if p.is_alive]

	def _get_agent_input(self, pid, agent):
		player = self.players[pid] if pid in self.players else None
		if not player or not player.is_alive:
			return

		logger.debug(f"[{player.name}] agent move....")
		chosen_move = agent.next_move()
		logger.debug(f"[{player.name}] agent move -> [{chosen_move}]")

		if not chosen_move:
			return # NO-OP action

		if chosen_move not in self.ACTION_CODES:
			logger.warn(f"Agent for '[{player.name}]' produced unxepected move '{chosen_move}', ignoring")
			return 

		return self.ACTION_CODES[chosen_move] if chosen_move in self.ACTION_CODES else None

	def _update_agent(self, delta_time: float, pid, agent, game_map):
		player = self.players[pid] if pid in self.players else None
		if not player or not player.is_alive:
			return

		player_state = self._player_state(pid, player)
		agent.update(game_map, player_state)


	def _player_state(self, id:PID, player:_Player):
		return PlayerState(id=id, ammo=player.ammo, hp=player.hp, location=player.pos, reward=player.reward, power=player.power) \
			if player else None

	def _try_add_fire(self, owner_pid:PID, pos:Point) -> bool:
		if not self._is_in_bounds(pos):
			return False
		
		if self._collision_list(pos, self.all_blocks) or self._collision_list(pos, self.bomb_list):
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
		
		hit_list = self._collision_list(player.pos, self.bomb_list)
		if hit_list: # Don't place a bomb on top of a bomb!
			return False

		player.ammo -= 1

		self.bomb_list.append(self._Bomb(pid, player.pos, self.BOMB_TTL, player.power))
		# TODO Update occupancy greed

		# Schedule respawn of an ammo for the next turn
		self._enqueue_effect(DelayedEffectType.SPAWN_AMMO, ttl=self.AMMO_RESPAWN_TTL)

		return True

	def _move(self, pid: PID, player: _Player, delta) -> bool:
		new_loc = (max(0, min(player.pos[0] + delta[0], self.column_count - 1)), max(0, min(player.pos[1] + delta[1], self.row_count-1)))
		if self._has_collision(new_loc):
			return False

		player.pos = new_loc
		
		return True

	def _pick_good_spots(self):
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
		for block in self.all_blocks:
			__safe_remove(block.pos)

		# Don't spawn ammo on top of another ammo
		for ammo in self.ammunition_list:
			__safe_remove(ammo.pos)

		# Don't spawn ammo on top of treasure ammo
		for ammo in self.treasure_list:
			__safe_remove(ammo.pos)

		# Don't spawn ammo on top of a bomb
		for ammo in self.bomb_list:
			__safe_remove(ammo.pos)

		return all_cells

	def _spawn_treasure(self):
		good_locations = self._pick_good_spots()
		if not good_locations:
			self._enqueue_effect(DelayedEffectType.SPAWN_TREASURE, ttl=random.randint(1, self.TREASURE_SPAWN_FREQUENCY_MIN))
			return False

		loc = random.choice(good_locations)
		self.treasure_list.append(Game._Treasure(loc))
		self._enqueue_effect(DelayedEffectType.SPAWN_TREASURE, ttl=random.randint(self.TREASURE_SPAWN_FREQUENCY_MIN, self.TREASURE_SPAWN_FREQUENCY_MAX))

		return True
	
	def _spawn_ammo(self):
		good_locations = self._pick_good_spots()
		if not good_locations:
			self._enqueue_effect(DelayedEffectType.SPAWN_AMMO, ttl=self.AMMO_RESPAWN_TTL)
			return False

		loc = random.choice(good_locations)
		self.ammunition_list.append(self._Ammunitation(loc, ttl=self.AMMO_PERISH_TTL, on_perish=lambda: self._enqueue_effect(DelayedEffectType.SPAWN_AMMO, ttl=self.AMMO_RESPAWN_TTL)))
		
		return True

	def _has_collision(self, pos:Point) -> bool:
		""" It checks if a player can move to a new location"""
		# Check if given postion overlaps with any of the blocks
		hit_list = self._collision_list(pos, self.all_blocks)

		# Check if given postion overlaps with any of the players
		# This makes players non-clipable
		hit_list += self._collision_list(pos, self.players.values())

		# Make bomb non-clipable
		hit_list += self._collision_list(pos, self.bomb_list)

		# Loop through each colliding sprite, remove it, and add to the score.
		return len(hit_list) > 0

