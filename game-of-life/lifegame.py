#!/usr/bin/env python2

from random import randrange, choice, shuffle, randint, seed, random
from math import cos, pi, sin, sqrt, atan, ceil, sqrt
from collections import deque, defaultdict

from fractions import Fraction
import operator
from game import Game
from copy import deepcopy
try:
    from sys import maxint
except ImportError:
    from sys import maxsize as maxint
    
EMPTY = -1

PLAYER_CELL = 'wb'
MAP_OBJECT = '-'
MAP_RENDER = PLAYER_CELL + MAP_OBJECT

class LifeGame(Game):
    def __init__(self, options=None):
        # setup options
        map_text = options['map']
        self.turns = int(options['turns'])
        self.sim_steps = int(options['sim_steps'])
        self.loadtime = int(options['loadtime'])
        self.turntime = int(options['turntime'])
        self.engine_seed = options.get('engine_seed', randint(-maxint-1, maxint))
        self.player_seed = options.get('player_seed', randint(-maxint-1, maxint))
        seed(self.engine_seed)
        
        self.cutoff_percent = options.get('cutoff_percent', 0.85)
        self.cutoff_turn = options.get('cutoff_turn', 150)
        
        self.scenario = options.get('scenario', False)
        
        map_data = self.parse_map(map_text)
        
        self.turn = 0
        self.num_players = map_data["num_players"]
        self.cells = {}
        
        self.player_to_begin = 0
        # used to cutoff games early
        self.cutoff = None
        self.cutoff_bot = None # Can be ant owner, FOOD or LAND
        self.cutoff_turns = 0
        # used to calculate the turn when the winner took the lead
        self.winning_bot = None
        self.winning_turn = 0
        # used to calculate when the player rank last changed
        self.ranking_bots = None
        self.ranking_turn = 0
        
        # initialize size
        self.height, self.width = map_data['size']

        # initialize map
        self.map = [[EMPTY]*self.width for _ in range(self.height)]

        # for new games alive cells are ignored 
        # for scenarios, the map file is followed exactly
        if self.scenario:
            # initialize alive cells
            for player, player_cells in map_data['cells'].items():
                for cell_loc in player_cells:
                    self.map[cell_loc[0]][cell_loc[1]] = player

        # original map to put in a replay data
        self.original_map = []
        for map_row in self.map:
            self.original_map.append(map_row[:])
                
        # initialize scores
        self.score = [0]*self.num_players
        self.bonus = [0]*self.num_players
        self.score_history = [[s] for s in self.score]

        # cache used by neighbourhood_offsets() to determine nearby squares
        self.offsets_cache = {}

        # used to track dead players
        self.killed = [False for _ in range(self.num_players)]

        # the engine may kill players before the game starts and this is needed
        # to prevent errors
        self.orders = [[] for i in range(self.num_players)]
        
    def get_default_map(self):
        return {
            'size':        (29, 29),
            'num_players': 2,
            'cells':       []
        }

    def parse_map(self, map_text):
        """ Parse the map_text into a more friendly data structure """
        if map_text is None:
            return self.get_default_map()
        
        cell_owners = None
        width = height = None
        cells = defaultdict(list)
        row = 0
        num_players = None
        char_empty = '-'

        for line in map_text.split('\n'):
            line = line.strip()

            # ignore blank lines and comments
            if not line or line[0] == '#':
                continue

            key, value = line.split(' ', 1)
            key = key.lower()
            if key == 'cols':
                width = int(value)
            elif key == 'rows':
                height = int(value)
            elif key == 'players':
                num_players = int(value)
                if num_players < 1 or num_players > 2:
                    raise Exception("map",
                                    "player count must be 1 or 2")
            elif key == 'm':
                if cell_owners is None:
                    if num_players is None:
                        raise Exception("map",
                                        "players count expected before map lines")
                    cell_owners = ['w', 'b'][:num_players]
                if len(value) != width:
                    raise Exception("map",
                                    "Incorrect number of cols in row %s. "
                                    "Got %s, expected %s."
                                    %(row, len(value), width))
                for col, c in enumerate(value):
                    if c in cell_owners:
                        cells[cell_owners.index(c)].append((row,col))
                    elif c != char_empty:
                        raise Exception("map",
                                        "Invalid character in map: %s" % c)
                row += 1
        if height != row:
            raise Exception("map",
                            "Incorrect number of rows.  Expected %s, got %s"
                            % (height, row))

        # look for alive cells to invalidate map for a game
        if not self.scenario and len(cells) > 0:
            raise Exception("map", 
                            "Only scenarios support alive cells in map files" % hill)

        return {
            'size':        (height, width),
            'num_players': num_players,
            'cells':       cells
        }
        
    def get_map_output(self):
        result = []
        for row in self.original_map:
            result.append(''.join([MAP_RENDER[col] for col in row]))
        return result
        
    def cnt_neighs(self, (row, col)):
        neighs = [(dx, dy) for dx in (-1,0,1) for dy in (-1,0,1) 
                 if not dx == dy == 0] # do not add original cell to its neigbours
                 
        cnt_neighs = [0] * self.num_players
        for (dx, dy) in neighs:
            if 0 <= row+dx < self.height and 0 <= col+dy < self.width: # check for boundary
                owner = self.map[row+dx][col+dy]
                if owner != EMPTY: 
                    cnt_neighs[owner] += 1
                    
        return cnt_neighs
                
        
    def simulate(self, steps_left):
        if steps_left <= 0:
            return
            
        to_kill, to_born = [],[]      
        for row_num, row in enumerate(self.map):
            for col_num, cell in enumerate(row):
                loc = (row_num, col_num)
                cnt_neighs = self.cnt_neighs(loc)
                # alive cells to kill
                if cell != EMPTY and not 1 < sum(cnt_neighs) < 4:
                    to_kill.append(loc)
                # new cells to born
                elif cell == EMPTY and sum(cnt_neighs) == 3:
                    to_born.append((loc, cnt_neighs.index(max(cnt_neighs))))
                    
        # apply changes
        for (row, col) in to_kill:
            self.map[row][col] = EMPTY
        for (row, col), owner in to_born:
            self.map[row][col] = owner
            
        self.simulate(steps_left-1)

    def player_cells(self, player):
        return [cell for cell in self.cells.values() if player == cell.owner]

    def parse_orders(self, player, lines):
        """ Parse orders from the given player

            Orders must be of the form: source destination num_ships
            row and col refer to the location of the agent you are ordering.
        """
        orders = []
        valid = []
        ignored = []
        invalid = []

        for line in lines:
            line = line.strip().lower()
            data = line.split()

            # validate data format
            if len(data) != 2:
                invalid.append((line, 'incorrectly formatted order'))
            else:
                row, col = data
                
                # validate the data types
                try:
                    row, col = int(row), int(col)
                except ValueError:
                    invalid.append((line, "orders should be integers"))
                    continue

                # if all is well, append to orders
                orders.append((row, col))
                valid.append(line)

        return orders, valid, ignored, invalid

    def validate_orders(self, player, orders, lines, ignored, invalid):
        """ Validate orders from a given player

            Cell location must exist
            Cell location must be empty
        """
        valid = []
        valid_orders = []
        for line, (row, col) in zip(lines, orders):
            if (row < 0 or row >= self.height or col < 0 or col >= self.width):
                invalid.append((line,'out of bounds'))
                continue
            if self.map[row][col] != EMPTY:
                invalid.append((line,'cell already occupied'))
                continue

            # this order is valid!
            valid_orders.append((row, col))
            valid.append(line)

        return valid_orders, valid, ignored, invalid
            
    def is_his_turn(self, player):
        """ Used to determine if player has right to make moves this turn
        """
        return len(self.cells) % 2 == player
        
    def do_orders(self):
        """ Execute player orders and handle conflicts
        """
        for player in range(self.num_players):
            if self.is_alive(player) and self.is_his_turn(player):
                for loc in self.orders[player]:
                    row, col = loc
                    self.map[row][col] = player
                    self.cells[loc] = Cell(loc, player, self.turn)

    def remaining_players(self):
        """ Return the players still alive """
        return [p for p in range(self.num_players) if self.is_alive(p)]

    # # Common functions for all games

    def game_over(self):
        """ Determine if the game is over

            Used by the engine to determine when to finish the game.
            A game is over when there are no players remaining, or a single
              winner remaining.
        """
        if len(self.remaining_players()) < 1:
            self.cutoff = 'extermination'
            return True
        elif len(self.remaining_players()) == 1:
            self.cutoff = 'lone survivor'
            return True
        else: return False

    def kill_player(self, player):
        """ Used by engine to signal that a player is out of the game """
        self.killed[player] = True

    def start_game(self):
        """ Called by engine at the start of the game """
        self.game_started = True

    def finish_game(self):
        """ Called by engine at the end of the game """

        if self.cutoff is None:
            # game ended normally, we can make life simulation
            self.cutoff = 'turn limit reached'
            self.simulate(self.sim_steps)
            # calculate scores (number of living cells for each player)      
            for player in range(self.num_players):
                for row in self.map:
                    self.score[player] += sum(cell == player for cell in row)
        else:
            # game ended because of bots failure
            for p in self.remaining_players():
                self.score[p] = 100

    def start_turn(self):
        """ Called by engine at the start of the turn """
        self.turn += 1
        self.orders = [[] for _ in range(self.num_players)]

    def finish_turn(self):
        """ Called by engine at the end of the turn """
        self.do_orders()

    def get_state(self):
        """ Get all state changes

            Used by engine for streaming playback
        """
        # no streaming for this game
        return ''

    def get_player_start(self, player):
        """ Get game parameters visible to players

            Used by engine to send bots startup info on turn 0
        """
        # hackerrank bots don't use it
        return ''

    def get_player_state(self, player):
        """ Get state changes visible to player

            Used by engine to send state to bots
        """
        cell_char = 'wb-'
        # first row contains character of the player 
        message = cell_char[player] + '\n'
        # here goes game grid
        message += '\n'.join(''.join(cell_char[cell] for cell in row) for row in self.map)
        return message

    def is_alive(self, player):
        """ Determine if player is still alive

            Used by engine to determine players still in the game
        """
        return not self.killed[player]

    def get_error(self, player):
        """ Returns the reason a player was killed

            Used by engine to report the error that kicked a player
              from the game
        """
        return ''

    def do_moves(self, player, moves):
        """ Called by engine to give latest player orders """
        orders, valid, ignored, invalid = self.parse_orders(player, moves)
        orders, valid, ignored, invalid = self.validate_orders(player, orders, valid, ignored, invalid)
        self.orders[player] = orders
        return valid, ['%s # %s' % ignore for ignore in ignored], ['%s # %s' % error for error in invalid]
        
    def get_moves_limit(self, player):
        """ Returns the orders limit for the player for current turn  
        
            Called by engine to determine if it should stop getting orders from bot
        """
        return 1
        

    def get_scores(self, player=None):
        """ Gets the scores of all players

            Used by engine for ranking
        """
        return self.score

    def order_for_player(self, player, data):
        """ Orders a list of items for a players perspective of player #

            Used by engine for ending bot states
        """
        # no ordering needed for this game
        return data

    def get_stats(self):
        """  Used by engine to report stats
        """
        # not stats for this game
        return {}

    def get_replay(self):
        """ Return a summary of the entire game

            Used by the engine to create a replay file which may be used
            to replay the game.
        """
        replay = {}
        # required params
        replay['revision'] = 1
        replay['players'] = self.num_players

        # optional params
        replay['loadtime'] = self.loadtime
        replay['turntime'] = self.turntime
        replay['turns'] = self.turns
        replay['engine_seed'] = self.engine_seed
        replay['player_seed'] = self.player_seed
        
        # map
        replay['map'] = {}
        replay['map']['rows'] = self.height
        replay['map']['cols'] = self.width
        replay['map']['data'] = self.get_map_output()
        
        # cells data
        cells = [[cell.loc[0], cell.loc[1], cell.spawn_turn, cell.owner] 
                for cell in self.cells.values()]
        replay['cells'] = sorted(cells, key = operator.itemgetter(2))

        # scores
        replay['scores'] = self.score_history
        replay['bonus'] = self.bonus
        replay['winning_turn'] = self.winning_turn
        replay['ranking_turn'] = self.ranking_turn
        replay['cutoff'] =  self.cutoff
        
        return replay
        
class Cell:
    def __init__(self, loc, owner, spawn_turn=None):
        self.loc = loc
        self.owner = owner
        self.spawn_turn = spawn_turn

    def __str__(self):
        return '(%s, %s, %s)' % (self.loc, self.owner, self.spawn_turn)
