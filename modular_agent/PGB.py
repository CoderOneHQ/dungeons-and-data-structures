'''
TEMPLATE for creating your own Agent to compete in
'Dungeons and Data Structures' at the Coder One AI Sports Challenge 2020.
For more info and resources, check out: https://bit.ly/aisportschallenge

BIO: 
Assign score to each cell (bombing it and moving to it separately) by
using a heuristic and move towards the best-scoring cell.
Check for easy kills of opponent.

'''

# import any external packages by un-commenting them
# if you'd like to test / request any additional packages - please check with the Coder One team
import random
import time
import numpy as np
from copy import deepcopy
from collections import deque
# import sklearn

# Yeeted from https://github.com/pshin05/Algorithm/blob/master/Graph/python/shortpath.py
class Vertex(object):
    """A vertex in a graph."""
    def __init__(self, name, adj):
        """Initialize with name and adj list"""
        super(Vertex, self).__init__()
        self.name = name
        self.adj = adj.copy()

    def __repr__(self):
        return "<%s: %s>" % (self.name, self.__dict__)
    
class Graph(object):
    """Dictionary of vertices
    >>> graph = Graph(FIG9_8)
    >>> graph
    <Graph:
     <v1: {'adj': {'v2': 2, 'v4': 1}, 'name': 'v1'}>
     <v2: {'adj': {'v4': 3, 'v5': 10}, 'name': 'v2'}>
     <v3: {'adj': {'v1': 4, 'v6': 5}, 'name': 'v3'}>
     <v4: {'adj': {'v3': 2, 'v5': 2, 'v6': 8, 'v7': 4}, 'name': 'v4'}>
     <v5: {'adj': {'v7': 6}, 'name': 'v5'}>
     <v6: {'adj': {}, 'name': 'v6'}>
     <v7: {'adj': {'v6': 1}, 'name': 'v7'}> >
    >>> graph['v1']
    <v1: {'adj': {'v2': 2, 'v4': 1}, 'name': 'v1'}>
    """
    def __init__(self, adj={}):
        super(Graph, self).__init__()
        self.vertices = {}
        for v in adj:
            self.vertices[v] = Vertex(v, adj[v])
            
    def __repr__(self):
        res = "<Graph:"
        for name, v in self.vertices.items():
            res += "\n %s" % v
        res += " >"
        return res
    
    def __getitem__(self, name):
        return self.vertices[name]

    def __iter__(self):
        return iter(self.vertices)

def dfs(G, V, depth=1):
    """Perform DFS on graph G at vertex V and determine
    if V and its adjacent vertices are articulation points
    by calculating and comparing V.num and V.low.
    Returns a list of articulation points of graph G.
    G : Graph instance
    V : Vertex instance
    depth : depth of DFST.
    """
    # update vertex attributes
    V.visited = True
    V.num = depth
    V.low = V.num        # for now
    V.child_count = 0    # useful for depth == 1 only
    
    # find num(adj) and low(adj) for all adj
    # also find all articulation points among descendents of V
    art_list = []
    for adj in V.adj:
        # get actual Vertex obj
        adjV = G.vertices[adj]
        # if adj not visited, then it is a child
        if not adjV.visited:
            V.child_count += 1
            art_list.extend( dfs(G, adjV, depth+1) )
        # update V.low
        if adjV.num < V.num:         # e(V, adj) is back edge
            V.low = min(V.low, adjV.num)
        else:                        # adj is child
            V.low = min(V.low, adjV.low)
    # determine if V is articulation point
    if depth == 1 and V.child_count > 1:
        art_list.append(V.name)
    elif depth > 1:
        for adj in V.adj:
            adjV = G.vertices[adj]
            if adjV.low >= V.num:
                art_list.append(V.name)
                break
    return art_list
    
def art_points(G, S=None):
    """Find all articulation points for G.
    If S is given, it is to be the root of DF spanning tree.
    Else, S is taken to be the first vertex of G.
    G : Graph instance
    S : start vertex name
    
    >>> art_points(Graph(FIG9_62), 'A')
    ['D', 'C']
    >>> art_points(Graph(FIG9_62), 'C')
    ['D', 'C']
    """
    if S is None:
        S = list(G.vertices.keys())[0]
    for V in G.vertices:
        G.vertices[V].visited = False
    V = G.vertices[S]
    return dfs(G, V)

class Agent:
    MAX_INT = 100000

    def __init__(self):
        '''
        Place any initialisation code for your agent here (if any)
        '''
        self.location = None
        self.opp_location = None
        self.game_state = None
        self.previous_action = None
        self.planned_action = None
        self.my_fire_list = []
        self.opp_fire_list = []
        self.my_score = 0
        self.my_ammo = 3
        self.opp_score = 0
        self.opp_ammo = 3
        self.my_hp = 3
        self.opp_hp = 3
        self.active_bombs = {}
        self.my_bombs = set()
        self.ore_hits_remaining = {}
        self.ammo_rounds_remaining = {}
        self.chests = {}
        self.history = []
        self.blacklist = set()
        self.soft_blocks = None
        self.ores = None
        self.keypoints = None
        self.endgame = False

        self.last_actions=deque([], maxlen=50)

    def next_move(self, game_state, player_state):
        '''
        This method is called each time your Agent is required to choose an action
        If you're just starting out or are new to Python, you can place all your
        code within the ### CODE HERE ### tags. If you're more familiar with Python
        and how classes and modules work, then go nuts.
        (Although we recommend that you use the Scrims to check your Agent is working)
        '''
        start = time.time()

        # print()
        # print()
        print()
        print(game_state.tick_number)

        self.last_actions.append(player_state.location)

        self.columns, self.rows = game_state.size

        ###### SET STATE VARIABLES ######
        self.prev_location = self.location
        self.prev_opp_location = self.opp_location
        self.game_state = game_state
        self.player_state = player_state
        self.location = self.player_state.location
        self.opp_location = self.game_state.opponents(self.player_state.id)[0]

        ## First tick state updates
        if not self.ore_hits_remaining:
            for ore in self.game_state.ore_blocks:
                self.ore_hits_remaining[ore] = 3

        ###### STATE UPDATE FUNCTIONS ######
        exploded_bombs = self.update_bomb_info()
        self.obstacles = self.get_obstacles()
        self.update_chest_times()
        self.update_chests()
        self.update_ammo()
        self.enemy_bombs = set(list(self.active_bombs.keys())) - self.my_bombs

        # # Do a check if the previous action has been executed successfully (async)
        # TODO: Sometimes this keeps happening, we should fix this...
        if self.previous_action is not None and self.previous_action != 'p':
            diffy = self.location[1] - self.prev_location[1]
            diffx = self.location[0] - self.prev_location[0]

            if self.previous_action == 'u' and diffy != 1:
                print(self.location, self.prev_location, self.tick, game_state.tick_number, game_state.entity_at(self.location))
                print('Previous action u was not executed sucessfully...')
                self.previous_action = None
                return ''
                # self.planned_action = 'u'
                # if diffx == 1:
                #     return 'l'
                # if diffx == -1:
                #     return 'r'
                # if diffy == -1:
                #     return 'u'
                # self.planned_action = None
                # return 'u'

            if self.previous_action == 'd' and diffy != -1:
                print(self.location, self.prev_location, self.tick, game_state.tick_number, game_state.entity_at(self.location))
                print('Previous action d was not executed sucessfully...')
                self.previous_action = None
                return ''
                # self.planned_action = 'd'
                # if diffx == 1:
                #     return 'l'
                # if diffx == -1:
                #     return 'r'
                # if diffy == 1:
                #     return 'd'
                # self.planned_action = None
                # return 'd'

            if self.previous_action == 'r' and diffx != 1:
                print(self.location, self.prev_location, self.tick, game_state.tick_number, game_state.entity_at(self.location))
                print('Previous action r was not executed sucessfully...')
                self.previous_action = None
                return ''
                # self.planned_action = 'r'
                # if diffx == -1:
                #     return 'r'
                # if diffy == 1:
                #     return 'd'
                # if diffy == -1:
                #     return 'u'
                # self.planned_action = None
                # return 'r'


            if self.previous_action == 'l' and diffx != -1:
                print(self.location, self.prev_location, self.tick, game_state.tick_number, game_state.entity_at(self.location))
                print('Previous action l was not executed sucessfully...')
                self.previous_action = None
                return ''
                # self.planned_action = 'l'
                # if diffx == 1:
                #     return 'l'
                # if diffy == 1:
                #     return 'd'
                # if diffy == -1:
                #     return 'u'
                # self.planned_action = None
                # return 'l'

        # self.blacklist = set()
        # print(set(self.history[-30:]))
        # if self.my_score < self.opp_score and len(set(self.history[-30:])) < 5:
        #     print('Deadlock situation')
        #     for (x, y) in set(self.history[-250:]):
        #         self.blacklist.add((x, y))

        # print(f'My position: {self.location}')
        # print(f'Opponent position: {self.opp_location}')
        # print(f'My Score {self.my_score} - {self.opp_score} Enemy Score')
        # print(f'My Ammo {self.my_ammo} - {self.opp_ammo} Enemy Ammo')
        # print(f'My HP {self.my_hp} - {self.opp_hp} Enemy HP')

        # for bomb in self.active_bombs:
        #     print(f'Bomb {bomb} is going to explode in {self.active_bombs[bomb]} rounds...')
        # # print(f'Enemy bombs: {self.enemy_bombs}')

        for ore in self.ore_hits_remaining:
            print(f'Ore {ore} has {self.ore_hits_remaining[ore]} hp remaining...')

        # for chest in self.chests:
        #     print(f'Chest at location {chest}...')

        # for ammo in self.ammo_rounds_remaining:
        #     print(f'Ammo {ammo} has {self.ammo_rounds_remaining[ammo]} remaining...')

        if self.planned_action:
            action = self.planned_action
            self.planned_action = None
            self.previous_action = action
            return action

        # Calculate distances from each walkable position to other tiles
        # We will use these distance maps very often for reward & cost calculation
        # Create an adjacency matrix.
        row_col_to_adj = lambda r, c: r * self.columns + c
        adj_to_row_col = lambda a: (a // self.columns, a % self.columns)
        A = np.ones((self.rows * self.columns, self.rows * self.columns)) * Agent.MAX_INT
        G_info = {}
        for y in range(self.rows):
            for x in range(self.columns):
                a = row_col_to_adj(y, x)
                A[a, a] = 0
                if (x, y) in self.obstacles - {self.location, self.opp_location}:
                    continue
                G_info[a] = {}
                # TODO: We can add a lower cost for tiles with ammo/chests
                for x2, y2 in self.get_empty_neighbours((x, y)):
                    G_info[a][row_col_to_adj(y2, x2)] = 1
                    A[a, row_col_to_adj(y2, x2)] = 1
        _distances = self.floyd_warshall_fastest(A)
        G = Graph(G_info)

        self.distances = {}
        for a1 in range(_distances.shape[0]):
            a1y, a1x = adj_to_row_col(a1)
            self.distances[(a1x, a1y)] = np.zeros((self.rows, self.columns))
            for a2 in range(_distances.shape[1]):
                a2y, a2x = adj_to_row_col(a2)
                self.distances[(a1x, a1y)][a2y, a2x] = _distances[a1, a2]

        # Find articulation points / cut vertices
        self.key_points = []
        art_points1 = set(art_points(G, S=row_col_to_adj(self.opp_location[1], self.opp_location[0])))
        art_points2 = set(art_points(G, S=row_col_to_adj(self.location[1], self.location[0])))
        for a in art_points1.union(art_points2):
            ay, ax = adj_to_row_col(a)
            self.key_points.append((ax, ay))
        # print(self.key_points)

        action = self.get_scores()
        # print(action)
        if action is None:
            action = ''

        if action == 'p':
            self.my_bombs.add(self.location)

        # Check if we are in endgame: all remaining soft & ore blocks
        # are unreachable by both players
        # print(self.distances[self.location][::-1, :])
        # print(self.distances[self.opp_location][::-1, :])
        game_soft_blocks = set(self.game_state.soft_blocks)
        game_ore_blocks = set(self.game_state.ore_blocks)
        all_destroyable_blocks = game_soft_blocks.union(game_ore_blocks)
        unreachable = set()
        for (x, y) in all_destroyable_blocks:
            reachable_tile = False
            for (x2, y2) in self.get_empty_neighbours((x, y)):
                if self.distances[self.location][y2, x2] != Agent.MAX_INT or self.distances[self.opp_location][y2, x2] != Agent.MAX_INT:
                    reachable_tile = True
                    break
            if not reachable_tile:
                unreachable.add((x, y))
        self.endgame = len(all_destroyable_blocks - unreachable) == 0
        # if self.endgame:
        #     print('We are in the endgame atm!')

        if len(set(self.last_actions)) <= 3 and len(list(self.last_actions)) == 50:
            if player_state.ammo > 0 and player_state.reward <= self.opp_score:
                # print('Deadlock!!!')
                action = 'p'
                self.my_bombs.add(self.location)

                moves = [
                    (self.location[1] + 1, self.location[0]),
                    (self.location[1] - 1, self.location[0]),
                    (self.location[1], self.location[0] + 1),
                    (self.location[1], self.location[0] - 1),
                ]
                best_a, max_n_tiles = None, 0
                for a, m in zip(['u', 'd', 'r', 'l'], moves):
                    # print(a, self.location, (m[1], m[0]), self.is_tile_walkable((m[1], m[0])))
                    if self.is_tile_walkable((m[1], m[0])):
                        self.obstacles.add(self.location)
                        dist = self.get_distances((m[1], m[0]))
                        self.obstacles -= {self.location}
                        n_tiles = sum([x != Agent.MAX_INT for y in dist for x in y ])
                        # print(a, n_tiles)
                        if n_tiles > max_n_tiles and n_tiles > 3:
                            max_n_tiles = n_tiles
                            best_a = a
                
                if best_a is None:
                    # print(f'No suited location found to move to')
                    return ''
                # print(f'Dropping bomb... Next move {best_a}')
                self.planned_action = best_a
            elif player_state.reward <= self.opp_score:
                action = random.choice(['u', 'd', 'r', 'l', ''])
            self.last_actions = deque(maxlen=50)

        print(self.location)
        print(f'Action = {action}')
        print(f'Total time needed: {time.time() - start} seconds', game_state.tick_number)
        self.previous_action = action
        self.tick = game_state.tick_number
        return action

    ### MAIN FUNCTIONS:
    ### Calculate score for each tile
    ### Plan moves towards that tile
    #############################
    def get_scores(self):
        # Create some sets for fast lookup
        game_soft_blocks = set(self.game_state.soft_blocks)
        game_ore_blocks = set(self.game_state.ore_blocks)
        game_ammo = set(self.game_state.ammo)
        game_chests = set(self.game_state.treasure)
        fire_list = set(self.my_fire_list).union(self.opp_fire_list)

        ###############################################################
        #                   REWARD CALCULATION                        #
        ###############################################################
        if not self.endgame:
            dominance_map = self.distance_to_enemy_map()
        else:
            # Prefer the center if we are in the endgame
            dominance_map = self.create_dominance_map()

        enclose_rewards, kill_rewards = self.enclose_enemy()
        bomb_block_scores = self.create_bomb_block_score_map()
        move_block_scores = self.create_move_block_score_map()
        # conv_move_rewards = self.convolve(move_block_scores)
        # conv_move_rewards[0, :] = 0
        # conv_move_rewards[-1, :] = 0
        # conv_move_rewards[:, -1] = 0
        # conv_move_rewards[:, 0] = 0
        # print(move_block_scores[::-1, :])
        # print(bomb_block_scores[::-1, :])

        move_rewards = .0001 * dominance_map
        all_splash_zone = set()
        for bomb in self.active_bombs:
            all_splash_zone = all_splash_zone.union(self.get_splash_zone(bomb))
        for y in range(self.rows):
            for x in range(self.columns):
                if (x, y) in all_splash_zone:
                    move_rewards[y, x] = 0
        move_rewards += 5 * move_block_scores + 20 * enclose_rewards
        bomb_rewards = 5 * bomb_block_scores + 500000 * kill_rewards


        for y in range(self.rows):
            for x in range(self.columns):
                if self.distances[self.location][y, x] >= Agent.MAX_INT:
                    move_rewards[y, x] = 0
                    bomb_rewards[y, x] = 0

        if self.player_state.ammo < 1:
            bomb_rewards[:, :] = 0

        if self.player_state.ammo == 1 and len(game_soft_blocks) > 0:
            bomb_rewards[:, :] = 500000 * kill_rewards

        # for x, y in self.blacklist:
        #     move_rewards[y, x] = -Agent.MAX_INT
        #     bomb_rewards[y, x] = -Agent.MAX_INT

        if self.location in self.get_hot_zone():
            # print('We need to move!!')
            move_rewards += 10
            for x, y in self.get_hot_zone():
                move_rewards[y, x] = -Agent.MAX_INT
                bomb_rewards[y, x] = -Agent.MAX_INT

        ###############################################################
        #                     COST CALCULATION                        #
        ###############################################################
        my_distances = self.distances[self.location]
        opp_distances = self.distances[self.opp_location]
        diffs = np.maximum(0, my_distances - opp_distances)
        bomb_cost_map = self.create_bomb_cost_map()
        danger_costs = self.create_dangerous_map()

        move_costs = 1 + 0.2 * my_distances + 1.5 * diffs + danger_costs
        bomb_costs = 1 + 0.2 * my_distances + 1. * diffs + danger_costs #+ .5 * bomb_cost_map

        move_scores = move_rewards / move_costs
        bomb_scores = bomb_rewards / bomb_costs

        # self.print_matrix(move_rewards)
        # print('-'*100)
        # self.print_matrix(move_costs)
        # print('-'*100)
        # self.print_matrix(bomb_rewards)
        # print('-'*100)
        # self.print_matrix(bomb_costs)
        # print('-'*100)

        # print('Moves:')
        # self.print_matrix(move_rewards)
        # print()
        # self.print_matrix(move_costs)
        # print()
        # # self.print_matrix(move_scores)
        # print('Bombs:')
        # self.print_matrix(bomb_rewards)
        # print()
        # self.print_matrix(bomb_costs)
        # print()
        # self.print_matrix(bomb_scores)
        # print()
        # print()
        # self.print_matrix(move_rewards)
        # print()
        # self.print_matrix(bomb_rewards)

        # print(f'Best move score = {np.max(move_scores)} || Best Bomb score = {np.max(bomb_scores)}')
        
        if np.max(move_scores) >= np.max(bomb_scores):
            best_move_y = np.argmax(move_scores) // self.columns
            best_move_x = np.argmax(move_scores) - (best_move_y * self.columns)
            self.history.append((best_move_x, best_move_y))

            # print(f'Moving to {(best_move_x, best_move_y)} with score {np.max(move_scores)}')

            diff_y = best_move_y - self.location[1]
            diff_x = best_move_x - self.location[0]

            # Plan bomb move
            if diff_y == 0 and diff_x == 0:
                return ''

            moves = [
                (self.location[1] + 1, self.location[0]),
                (self.location[1] - 1, self.location[0]),
                (self.location[1], self.location[0] + 1),
                (self.location[1], self.location[0] - 1),
            ]
            distances = []
            actions = []
            for m, a in zip(moves, ['u', 'd', 'r', 'l']):
                not_forbidden = self.location in self.get_hot_zone() or ((m[1], m[0]) not in self.get_hot_zone())
                if self.game_state.is_in_bounds((m[1], m[0])) and not_forbidden:
                    try:
                        distances.append(self.distances[(best_move_x, best_move_y)][m[0]][m[1]])
                        actions.append(a)
                    except:
                        continue
            if len(distances) == 0 or min(distances) == Agent.MAX_INT:
                return ''

            # print(distances, actions)

            ix = np.arange(len(distances))
            np.random.shuffle(ix)
            distances = np.array(distances)[ix]
            actions = np.array(actions)[ix]
            return actions[np.argmin(distances)]

        else:
            best_bomb_y = np.argmax(bomb_scores) // self.columns
            best_bomb_x = np.argmax(bomb_scores) - (best_bomb_y * self.columns)
            # print(f'Bombing {(best_bomb_x, best_bomb_y)} with score {np.max(bomb_scores)}')
            self.history.append((best_bomb_x, best_bomb_y))

            diff_y = best_bomb_y - self.location[1]
            diff_x = best_bomb_x - self.location[0]

            # Plan bomb move
            if diff_y == 0 and diff_x == 0 and (best_bomb_x, best_bomb_y) not in self.get_hot_zone():
                
                moves = [
                    (self.location[1] + 1, self.location[0]),
                    (self.location[1] - 1, self.location[0]),
                    (self.location[1], self.location[0] + 1),
                    (self.location[1], self.location[0] - 1),
                ]
                best_a, max_n_tiles = None, 0
                for a, m in zip(['u', 'd', 'r', 'l'], moves):
                    # print(a, self.location, (m[1], m[0]), self.is_tile_walkable((m[1], m[0])))
                    if self.is_tile_walkable((m[1], m[0])):
                        self.obstacles.add(self.location)
                        dist = self.get_distances((m[1], m[0]))
                        self.obstacles -= {self.location}
                        n_tiles = sum([x != Agent.MAX_INT for y in dist for x in y ])
                        # print(a, n_tiles)
                        if n_tiles > max_n_tiles and n_tiles > 3:
                            max_n_tiles = n_tiles
                            best_a = a
                
                if best_a is None:
                    # print(f'No suited location found to move to')
                    return ''
                # print(f'Dropping bomb... Next move {best_a}')
                self.planned_action = best_a
                return 'p'

            moves = [
                (self.location[1] + 1, self.location[0]),
                (self.location[1] - 1, self.location[0]),
                (self.location[1], self.location[0] + 1),
                (self.location[1], self.location[0] - 1),
            ]
            distances = []
            actions = []
            for m, a in zip(moves, ['u', 'd', 'r', 'l']):
                not_forbidden = self.location in self.get_hot_zone() or ((m[1], m[0]) not in self.get_hot_zone())
                if self.game_state.is_in_bounds((m[1], m[0])) and not_forbidden:
                    try:
                        distances.append(self.distances[(best_bomb_x, best_bomb_y)][m[0]][m[1]])
                        actions.append(a)
                    except:
                        continue
            if len(distances) == 0 or min(distances) == Agent.MAX_INT:
                return ''

            # print(distances, actions)

            ix = np.arange(len(distances))
            np.random.shuffle(ix)
            distances = np.array(distances)[ix]
            actions = np.array(actions)[ix]
            return actions[np.argmin(distances)]


    ### SCORING FUNCTIONS
    #############################
    def enclose_enemy(self, radius=2):
        enclose_rewards = np.zeros((self.rows, self.columns))
        kill_rewards = np.zeros((self.rows, self.columns))

        explosion_zone = set()
        for bomb in self.active_bombs:
            explosion_zone = explosion_zone.union(self.get_splash_zone(bomb))
        my_distances = self.distances[self.location]

        self.obstacles -= {self.location}
        opp_distances = self.get_distances(self.opp_location)
        self.obstacles.add(self.location)

        # TODO: If we are currently blocking the enemy, we should give reward to our current location
        partition1 = list(zip(*np.where(self.distances[self.opp_location] != Agent.MAX_INT)))
        partition2 = list(zip(*np.where(opp_distances != Agent.MAX_INT)))
        partition2 = set(partition2) - set(partition1)
        if len(partition2) > len(partition1) and len(partition1) <= 15:
            best_point, best_score = self.location, len(partition2) - len(partition1) + 1
        else:
            best_point, best_score = None, 0

        # print(partition1)
        trapped = len({(x, y) for y, x in partition1} - explosion_zone - {self.opp_location}) == 0
        # if trapped:
        #     print('Player is completely trapped')

        if self.player_state.ammo == 0 and self.my_score <= self.opp_score:
            return enclose_rewards, kill_rewards

        radius_points = set()
        for y in range(max(0, self.location[1] - radius), min(self.rows, self.location[1] + radius)):
            for x in range(max(0, self.location[0] - radius), min(self.columns, self.location[0] + radius)):
                radius_points.add((x, y))

        for (x, y) in set(self.key_points).union(radius_points):
            if (x, y) != self.location and ((x, y) in self.obstacles or self.distances[self.location][y, x] == Agent.MAX_INT):
                continue

            if (x, y) != self.location and self.distances[self.location][y, x] - 1 > self.distances[self.opp_location][y, x]:
                continue

            self.obstacles -= {self.location}
            self.obstacles.add((x, y))
            new_opp_distances = self.get_distances((self.opp_location))
            self.obstacles -= {(x, y)}
            self.obstacles.add(self.location)

            # Partition 1 is what the opponent can still reach
            partition1 = list(zip(*np.where(new_opp_distances != Agent.MAX_INT)))
            # Partition 2 is what the opponent can no longer reach
            partition2 = list(zip(*np.where(opp_distances != Agent.MAX_INT)))
            partition2 = set(partition2) - set(partition1)

            if len(partition1) > 15:
                continue

            kill = len({(x, y) for y, x in partition1} - explosion_zone.union(self.get_splash_zone((x, y)))) == 0
            if (x, y) == self.location and kill and self.player_state.ammo > 0:
                # print('------------> I am going in for the kill!')
                kill_rewards[y, x] = 1

            if len(partition2) - len(partition1) + 1 > best_score:
                best_score = len(partition2) - len(partition1) + 1
                best_point = (x, y)
                # print(best_point, best_score)

        if best_point is not None:
            # print(f'------------> Enclosing enemy on {best_point}')
            enclose_rewards[best_point[1], best_point[0]] = 1

        return enclose_rewards, kill_rewards

    def create_dominance_map(self):
        dominance_map = np.zeros((self.rows, self.columns))
        for y in range(self.rows):
            for x in range(self.columns):
                dominance_map[y, x] += (9 - min(
                    abs(y - 4) + abs(x - 5),
                    abs(y - 4) + abs(x - 6),
                    abs(y - 5) + abs(x - 5),
                    abs(y - 5) + abs(x - 6),
                ))
        return dominance_map

    def distance_to_enemy_map(self):
        distance_map = deepcopy(self.distances[self.opp_location])
        distance_map[np.where(distance_map == Agent.MAX_INT)] = np.nan 
        _max = np.nanmax(distance_map)
        distance_map[np.where(np.isnan(distance_map))] = _max
        distance_map = np.max(distance_map) - distance_map
        return distance_map

    def create_bomb_block_score_map(self, ore_rewards=[0, 15, 0.25, 1]):
        game_soft_blocks = set(self.game_state.soft_blocks)
        game_ore_blocks = set(self.game_state.ore_blocks)

        my_free_tiles = np.sum(self.distances[self.location] != Agent.MAX_INT)

        ore_hits_remaining = deepcopy(self.ore_hits_remaining)
        bomb_splash = set()
        for bomb in self.active_bombs:
            hit_ores = self.get_splash_zone(bomb).intersection(game_ore_blocks)
            for ore in hit_ores:
                ore_hits_remaining[ore] = max(0, ore_hits_remaining[ore] - 1)
            bomb_splash = bomb_splash.union(self.get_splash_zone(bomb))

        bomb_block_scores = np.zeros((self.rows, self.columns))
        for y in range(self.rows):
            for x in range(self.columns):
                splash = self.get_splash_zone((x, y))
                hit_softs = splash.intersection(game_soft_blocks)
                filtered_hit_softs = set()
                for soft in hit_softs:
                    if soft not in bomb_splash:
                        filtered_hit_softs.add(soft)
                hit_softs = filtered_hit_softs

                soft_reward = 2 * len(hit_softs)
                ore_reward = 0
                for ore in splash.intersection(game_ore_blocks):
                    ore_reward += ore_rewards[ore_hits_remaining[ore]]

                bomb_block_scores[y, x] += (soft_reward + ore_reward)

                # if my_free_tiles < 40:
                #     free_tile_score = 0
                #     for block in splash.intersection(game_ore_blocks.union(game_soft_blocks)):
                #         free_tile_score += np.sum(self.distances[block] != Agent.MAX_INT) / 120
                #     bomb_block_scores[y, x] += my_free_tiles

        return bomb_block_scores

    def ammo_score(self):
        return max(1, (5 - self.player_state.ammo)) / 3

    def create_move_block_score_map(self, ammo_reward=0.5):
        game_ammo = set(self.game_state.ammo)
        game_chests = set(self.game_state.treasure)

        move_block_scores = np.zeros((self.rows, self.columns))
        for x, y in game_ammo:
            move_block_scores[y, x] += self.ammo_score()
        for x, y in game_chests:
            move_block_scores[y, x] += 1
        return move_block_scores

    def create_bomb_cost_map(self):
        game_ammo = set(self.game_state.ammo)

        # If we have no ammo, then we shouldn't plan to place any
        if self.player_state.ammo == 0:
            return np.ones((self.rows, self.columns)) * Agent.MAX_INT

        # If not a lot of ammo is available on the map, we add penalty
        ammo_cost = 10 / max(1, len(self.game_state.ammo))
        bomb_costs = np.ones((self.rows, self.columns)) * ammo_cost

        my_distances = self.distances[(self.location[0], self.location[1])]

        # Cost to place bomb is equal to distance to the 
        # placement position and distance to ammo from either
        # current position or placement position
        for y in range(self.rows):
            for x in range(self.columns):
                best_dist = 25
                if (x, y) not in self.obstacles:
                    for ammo in game_ammo:
                        bomb_dist = self.distances[(x, y)][ammo[1], ammo[0]]
                        my_dist = my_distances[ammo[1], ammo[0]]
                        d = min(bomb_dist, my_dist)
                        if d < best_dist:
                            best_dist = d
                bomb_costs[y, x] += best_dist
        return bomb_costs

    def create_dangerous_map(self, splash_cost=100):
        danger_costs = np.zeros((self.rows, self.columns))
        for x, y in self.get_hot_zone():
            danger_costs[y, x] += 5*Agent.MAX_INT
            danger_costs[y, x] += 5*Agent.MAX_INT
        for bomb in self.active_bombs:
            if self.active_bombs[bomb] > 5:
                for x, y in self.get_splash_zone(bomb):
                    danger_costs[y, x] += (35 - self.active_bombs[bomb]) * splash_cost
                if bomb not in self.my_bombs:
                    danger_costs[y, x] += (splash_cost + 1)
        return danger_costs

    ### HELPER FUNCTIONS
    #############################
    def check_and_convert_adjacency_matrix(self, adjacency_matrix):
        mat = np.asarray(adjacency_matrix)

        (nrows, ncols) = mat.shape
        assert nrows == ncols
        n = nrows

        assert (np.diagonal(mat) == 0.0).all()

        return (mat, n)

    def floyd_warshall_fastest(self, adjacency_matrix):
        (mat, n) = self.check_and_convert_adjacency_matrix(adjacency_matrix)
        for k in range(n):
            mat = np.minimum(mat, mat[np.newaxis,k,:] + mat[:,k,np.newaxis]) 
        return mat

    def convolve(self, a, kernel=np.array([[0,0.5,0],[0.5,1,0.5],[0,0.5,0]])):
        arraylist = []
        for y in range(3):
            temparray = np.copy(a)
            temparray = np.roll(temparray, y - 1, axis=0)
            for x in range(3):
                temparray_X = np.copy(temparray)
                temparray_X = np.roll(temparray_X, x - 1, axis=1)*kernel[y,x]
                arraylist.append(temparray_X)

        arraylist = np.array(arraylist)
        arraylist_sum = np.sum(arraylist, axis=0)
        return arraylist_sum

    def get_obstacles(self):
        obstacles = set()
        obstacles = obstacles.union(self.game_state.all_blocks)
        obstacles = obstacles.union(self.game_state.bombs)
        obstacles = obstacles.union({self.opp_location, self.location})
        return obstacles

    def update_chest_times(self):
        for chest in self.game_state.treasure:
            if chest not in self.chests:
                self.chests[chest] = 2000
            self.chests[chest] -= 1

    def update_chests(self):
        picked_up_chests = set(self.chests.keys()) - set(self.game_state.treasure)
        for chest in picked_up_chests:
            if chest == self.location:
                self.my_score += 1
            elif self.chests[chest]>0:
                self.opp_score += 1
            del self.chests[chest]

    def update_ammo(self):
        game_ammo = set(self.game_state.ammo)
        picked_up_ammo = set(list(self.ammo_rounds_remaining.keys())) - game_ammo
        for ammo in picked_up_ammo:
            if ammo == self.location:
                self.my_ammo += 1
            elif ammo == self.opp_location:
                self.opp_ammo += 1

        for ammo in game_ammo:
            if ammo not in self.ammo_rounds_remaining:
                self.ammo_rounds_remaining[ammo] = 175
            else:
                self.ammo_rounds_remaining[ammo] -= 1

        for ammo in list(self.ammo_rounds_remaining.keys()):
            if ammo not in game_ammo:
                # print(f'Ammo at {ammo} dissapeared...')
                del self.ammo_rounds_remaining[ammo]

    def update_bomb_info(self):

        # Decrease lifetime of active bombs by 1
        for bomb in self.active_bombs:
            self.active_bombs[bomb] -= 1

        # Add new bombs to our set
        for bomb in set(self.game_state.bombs) - set(self.active_bombs.keys()):
            # print(f'Detected new bomb: {bomb}')
            if bomb in self.my_bombs:
                self.my_ammo -= 1
            else:
                self.opp_ammo -= 1
            self.active_bombs[bomb] = 35

        if self.location in self.my_fire_list:
            self.my_hp -= 1
        if self.location in self.opp_fire_list:
            self.my_hp -= 1
            self.opp_score += 25

        if self.opp_location in self.my_fire_list:
            self.opp_hp -=1
            self.my_score += 25

        if self.opp_location in self.opp_fire_list:
            self.opp_hp -= 1

        self.my_fire_list = []
        self.opp_fire_list = []
        # # Check the tiles in my fire_list if we hit someone
        # for tile in self.my_fire_list:
        #     my_hit = self.location == tile
        #     opp_hit = self.opp_location == tile
        #     self.my_hp -= int(my_hit)
        #     self.opp_hp -= int(opp_hit)
        #     self.my_score += 25 * opp_hit
        #     if tile in self.my_bombs:
        #         self.my_bombs -= {tile}
        #     if tile in self.active_bombs and self.active_bombs[tile] <= 0:
        #         del self.active_bombs[tile]

        # self.my_fire_list = []

        # # Same for opponent's fire list
        # for tile in self.opp_fire_list:
        #     my_hit = self.location == tile
        #     opp_hit = self.opp_location == tile
        #     self.my_hp -= int(my_hit)
        #     self.opp_hp -= int(opp_hit)
        #     self.opp_score += 25 * my_hit
        #     if tile in self.active_bombs and self.active_bombs[tile] <= 0:
        #         del self.active_bombs[tile]

        # self.opp_fire_list = []

        # Get the bombs that are no longer in the game state
        exploded_bombs = set(self.active_bombs.keys()) - set(self.game_state.bombs)

        # # Set timer of bombs in splash range of exploded bombs to 1
        # for bomb in exploded_bombs:
        #     for splash_bomb in self.get_splash_zone(bomb).intersection(list(self.active_bombs.keys())):
        #         exploded_bombs = exploded_bombs.union({splash_bomb})

        # Blocks get destroyed instantly so we use exploded bombs

        # Update the ticks for our bombs
        self.soft_blocks = set(self.game_state.soft_blocks)
        self.ores = set(self.game_state.ore_blocks)

        for bomb in exploded_bombs:
            splash_zone = self.get_splash_zone(bomb)
            # print("splash", bomb, "zone", splash_zone)
            for hit_bomb in splash_zone.intersection(self.active_bombs) - {bomb}:
                self.active_bombs[hit_bomb] = min(1, self.active_bombs[hit_bomb])
            # print(splash_zone)
            # print(self.soft_blocks)
            bomb_score = len(self.soft_blocks.intersection(splash_zone)) * 2
            ores_hit = self.ores.intersection(splash_zone)
            for ore in ores_hit:
                if self.ore_hits_remaining[ore] == 1:
                    if bomb in self.my_bombs:
                        self.my_score += 10
                    else:
                        self.opp_score += 10

                self.ore_hits_remaining[ore] -= 1
                self.ore_hits_remaining[ore] = max(self.ore_hits_remaining[ore], 0)

            # print(f'{bomb} exploded! (is mine? {bomb in self.my_bombs}) {bomb_score}')
            if bomb in self.my_bombs:
                self.my_score += bomb_score
            else:
                self.opp_score += bomb_score

            #my_hit = self.location in splash_zone
            #opp_hit = self.opp_location in splash_zone
            #print("my_loc", player_state.location, self.location)
            #self.my_hp -= int(my_hit)
            #self.opp_hp -= int(opp_hit)
            #if bomb in self.my_bombs:
            #    self.my_score += 25 * opp_hit
            #    self.my_bombs -= {bomb}
            #else:
            #    self.opp_score += 25 * my_hit

            # Add splash zone of exploded bombs to a fire list for next round
            if bomb in self.my_bombs:
                self.my_fire_list += list(splash_zone)
            else:
                self.opp_fire_list += list(splash_zone)

            del self.active_bombs[bomb]

        return exploded_bombs

    def print_matrix(self, matrix):
        for row in matrix[::-1]:
            print(list(map(lambda i: '{:>4f}'.format(i), row)))

    def get_distances(self, start):
        distances = np.ones((self.rows, self.columns)) * Agent.MAX_INT
        distances[start[1], start[0]] = 0

        frontier = {start}
        while len(frontier):
            curr_pos = frontier.pop()
            for new_pos in self.get_empty_neighbours(curr_pos):
                new_dist = distances[curr_pos[1], curr_pos[0]] + 1
                if new_dist < distances[new_pos[1], new_pos[0]]:
                    distances[new_pos[1], new_pos[0]] = new_dist
                    frontier.add(new_pos)

        return distances

    def get_hot_zone(self, thresholds=[0, 15, 11, 8]):
        zone = set()
        # find all active bombs
        for bomb in self.active_bombs:
            if self.active_bombs[bomb] < thresholds[self.player_state.hp]:
                for t in self.get_splash_zone(bomb):
                    zone.add(t)

        # find chaining bombs
        changed = True
        while changed:
            changed = False
            for bomb in self.active_bombs:
                if bomb in zone:
                    for t in self.get_splash_zone(bomb):
                        if t not in zone:
                            changed = True
                            zone.add(t)
        return zone.union(set(self.my_fire_list)).union(set(self.opp_fire_list))

    def get_splash_zone(self, bomb):
        # bombs are blocked by blocks and other bombs
        # bombs are not blocked by chests and ammo
        cover = set(self.game_state.all_blocks)
        cover = cover.union(self.game_state.bombs)

        one_right = (bomb[0]+1, bomb[1])
        one_left = (bomb[0]-1, bomb[1])
        one_up = (bomb[0], bomb[1]+1)
        one_down = (bomb[0], bomb[1]-1)
        same_pos = (bomb[0], bomb[1])
        splash = [one_up, one_down, one_left, one_right, same_pos]

        if one_up not in cover:
            splash.append((bomb[0], bomb[1]+2))
        if one_down not in cover:
            splash.append((bomb[0], bomb[1]-2))
        if one_right not in cover:
            splash.append((bomb[0]+2, bomb[1]))
        if one_left not in cover:
            splash.append((bomb[0]-2, bomb[1]))

        zone = set()
        for tile in splash:
            if self.game_state.is_in_bounds(tile):
                zone.add(tile)
        return zone

    def in_splash_zone(self, tile):
        zone = self.get_hot_zone()
        if tile not in zone:
            return False
        return True

    def is_tile_walkable(self, tile):
        if not self.game_state.is_in_bounds(tile):
            return False

        if tile not in self.obstacles:
            return True

        # if in bounds and in obstacles: check if it is a chest or ammo
        game_ammo = set(self.game_state.ammo)
        game_chests = set(self.game_state.treasure)

        if tile in game_ammo or tile in game_chests:
            return True

        return False

    def get_empty_neighbours(self, tile):
        tile_up = (tile[0], tile[1]+1)
        tile_down = (tile[0], tile[1]-1)
        tile_left = (tile[0]-1, tile[1])
        tile_right = (tile[0]+1, tile[1])

        all_surrounding_tiles = [tile_up, tile_down, tile_left, tile_right]
        valid_surrounding_tiles = []

        for t in all_surrounding_tiles:
            if self.is_tile_walkable(t):
                valid_surrounding_tiles.append(t)

        return valid_surrounding_tiles

    def get_inbound_neighbours(self, tile):
        tile_up = (tile[0], tile[1]+1)
        tile_down = (tile[0], tile[1]-1)
        tile_left = (tile[0]-1, tile[1])
        tile_right = (tile[0]+1, tile[1])

        all_surrounding_tiles = [tile_up, tile_down, tile_left, tile_right]
        valid_surrounding_tiles = set()

        for t in all_surrounding_tiles:
            if self.game_state.is_in_bounds(t):
                valid_surrounding_tiles.add(t)

        return valid_surrounding_tiles

    def move_to_neighbour(self, location, tile):

        actions = ['', 'u', 'd', 'l','r','p']

        # see where the tile is relative to our current location
        diff = tuple(x-y for x, y in zip(self.location, tile))

        # return the action that moves in the direction of the tile
        if diff == (0,1):
            action = 'd'
        elif diff == (1,0):
            action = 'l'
        elif diff == (0,-1):
            action = 'u'
        elif diff == (-1,0):
            action = 'r'
        else:
            action = ''

        return action

