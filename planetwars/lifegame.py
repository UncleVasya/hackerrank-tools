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

class LifeGame(Game):
    def __init__(self, options=None):
        # setup options
        map_text = options['map']
        self.turns = int(options['turns'])
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
                    self.add_initial_ant(ant_loc, player)
            self.original_map = []
            for map_row in self.map:
                self.original_map.append(map_row[:])

        # initialize scores
        self.score = [0]*self.num_players
        self.bonus = [0]*self.num_players
        self.score_history = [[s] for s in self.score]

        # cache used by neighbourhood_offsets() to determine nearby squares
        self.offsets_cache = {}

        # used to track dead players, ants may still exist, but orders are not processed
        self.killed = [False for _ in range(self.num_players)]

        # used to give a different ordering of players to each player;
        # initialized to ensure that each player thinks they are player 0
        self.switch = [[None]*self.num_players + list(range(-5,0))
                       for i in range(self.num_players)]
        for i in range(self.num_players):
            self.switch[i][i] = 0

        # the engine may kill players before the game starts and this is needed
        # to prevent errors
        self.orders = [[] for i in range(self.num_players)]

#        raise Exception(self.grid)
        ### collect turns for the replay
        self.replay_data = ""
        self.turn_strings = []

    def parse_map(self, map_text):
        """ Parse the map_text into a more friendly data structure """
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
        
    def born_cell(self, loc, owner):
        cell = Cell(loc, owner, self.turn)
        row, col = loc
        self.map[row][col] = owner
        self.cells[loc] = cell
        return cell
    
    def kill_cell(self, cell, ignore_error=False):
        loc = cell.loc
        self.map[loc[0]][loc[1]] = EMPTY
        return self.cells.pop(loc)

    def player_cells(self, player):
        return [cell for cell in self.cells.values() if player == cell.owner]


    # def render_changes(self, player):
        # """ Create a string which communicates the updates to the state
        # """
        # updates = self.get_state_changes()
        # visible_updates = []
        # # next list all transient objects
        # for update in updates:
            # visible_updates.append(update)
        # visible_updates.append([]) # newline
        # return '\n'.join(' '.join(map(str,s)) for s in visible_updates)
        
    # def switch_pov(self, player_id, pov):
        # if pov < 0:
            # return player_id
        # if player_id == pov:
            # return 1
        # if player_id == 1:
            # return pov
        # return player_id
        # # return player_id
  
    def serialize_game_state(self, pov):
        """ Returns a string representation of the entire game state
        """
        cell_char = 'wb-'
        # first row contains character of the player 
        message = cell_char[pov] + '\n'
        # here goes game grid
        message += '\n'.join(''.join(cell_char[cell] for cell in row) for row in self.map) + '\n'
        return message.replace("\n\n", "\n")
  
    # # Turns a list of planets into a string in playback format. This is the initial
    # # game state part of a game playback string.
    # def planet_to_playback_format(self):
        # planet_strings = []
        # for p in self.planets:
            # planet_strings.append(str(p["x"]) + "," + str(p["y"]) + "," + \
                # str(p["owner"]) + "," + str(p["num_ships"]) + "," + \
                # str(p["growth_rate"]))
        # return ":".join(planet_strings)
    
    # # Turns a list of fleets into a string in playback format. 
    # def fleets_to_playback_format(self):
        # fleet_strings = []
        # for p in self.fleets:
            # fleet_strings.append(str(p["owner"]) + "." + str(p["num_ships"]) + "." + \
                # str(p["source"]) + "." + str(p["destination"]) + "." + \
                # str(p["total_trip_length"]) + "." + str(p["turns_remaining"]))
        # return ",".join(fleet_strings)

    # # Represents the game state in frame format. Represents one frame.
    # def frame_representation(self):
        # planet_string = \
            # ",".join([str(p["owner"]) + "." + str(p["num_ships"]) for p in self.planets])
        # return planet_string + "," + self.fleets_to_playback_format()
  
    # def get_state_changes(self):
        # """ Return a list of all transient objects on the map.

            # Changes are sorted so that the same state will result in the same
            # output.
        # """
        # changes = self.frame_representation()
# #        changes.extend(sorted(
# #            ['p', p["player_id"]]
# #            for p in self.players if self.is_alive(p["player_id"])))
        # # changes.extend(sorted(
            # # ['a', a["row"], a["col"], a["heading"], a["owner"]]
            # # for a in self.agents))
        # # changes.extend(sorted(
            # # ['d', a["row"], a["col"], a["heading"], a["owner"]]
            # # for a in self.killed_agents))
        # return changes

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

    # def planetwars_orders(self, player):
        # """ Enacts orders for the Planet Wars game
        # """
        # player_orders = self.orders[player]
        # for order in player_orders:
            # (player_id, src, dest, num_ships) = order
            # source_planet = self.planets[src]
            # source_planet["num_ships"] -= num_ships
            # self.planets[src] = source_planet # not sure this is needed
            # if src not in self.temp_fleets:
                # self.temp_fleets[src] = {}
            # if dest not in self.temp_fleets[src]:
                # self.temp_fleets[src][dest] = 0
            # self.temp_fleets[src][dest] += num_ships
            
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
                    self.born_cell(loc, player)

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
        
        # append turn 0 to replay
        #self.replay_data = self.planet_to_playback_format() + "|"

    def finish_game(self):
        """ Called by engine at the end of the game """
#        players = self.remaining_players()
#        if len(players) == 1:
#            for player in range(self.num_players):
#                self.score[player] += self.bonus[player]

        # for i, s in enumerate(self.score):
            # self.score_history[i].append(s)
        # self.replay_data += ":".join(self.turn_strings)

        # check if a rule change lengthens games needlessly
        if self.cutoff is None:
            self.cutoff = 'turn limit reached'

    def start_turn(self):
        """ Called by engine at the start of the turn """
        self.turn += 1
        self.orders = [[] for _ in range(self.num_players)]
#        for player in self.players:
#            self.begin_player_turn(player)

    # def update_scores(self):
        # """ Update the record of players' scores
        # """
        # for p in range(self.num_players):
            # self.score[p] = self.num_ships_for_player(p)

    def finish_turn(self):
        """ Called by engine at the end of the turn """
        self.do_orders()
        ### append turn to replay
        # self.turn_strings.append(self.get_state_changes())

    # def get_state(self):
        # """ Get all state changes

            # Used by engine for streaming playback
        # """
        # updates = self.get_state_changes()
        # updates.append([]) # newline
        # return '\n'.join(' '.join(map(str,s)) for s in updates)

    def get_player_start(self, player):
        """ Get game parameters visible to players

            Used by engine to send bots startup info on turn 0
        """
        return ''

    def get_player_state(self, player):
        """ Get state changes visible to player

            Used by engine to send state to bots
        """
        return self.serialize_game_state(player)
        
    # def num_ships_for_player(self, player):
        # return sum([p["num_ships"] for p in self.planets if p["owner"] == player+1]) + \
            # sum([f["num_ships"] for f in self.fleets if f["owner"] == player+1])

    def is_alive(self, player):
        """ Determine if player is still alive

            Used by engine to determine players still in the game
        """
        return not self.killed[player]

    # def get_error(self, player):
        # """ Returns the reason a player was killed

            # Used by engine to report the error that kicked a player
              # from the game
        # """
        # return ''

    def do_moves(self, player, moves):
        """ Called by engine to give latest player orders """
        orders, valid, ignored, invalid = self.parse_orders(player, moves)
        orders, valid, ignored, invalid = self.validate_orders(player, orders, valid, ignored, invalid)
        self.orders[player] = orders
        return valid, ['%s # %s' % ignore for ignore in ignored], ['%s # %s' % error for error in invalid]

    # def get_scores(self, player=None):
        # """ Gets the scores of all players

            # Used by engine for ranking
        # """
        # if player is None:
            # return self.score
        # else:
            # return self.order_for_player(player, self.score)

    # def order_for_player(self, player, data):
        # """ Orders a list of items for a players perspective of player #

            # Used by engine for ending bot states
        # """
        # s = self.switch[player]
        # return [None if i not in s else data[s.index(i)]
                # for i in range(max(len(data),self.num_players))]

    def get_stats(self):
        """  Used by engine to report stats
        """
        stats = {}
        return stats

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

        # scores
        replay['scores'] = self.score_history
        replay['bonus'] = self.bonus
        replay['winning_turn'] = self.winning_turn
        replay['ranking_turn'] = self.ranking_turn
        replay['cutoff'] =  self.cutoff
        
        ### 
        replay['data'] = self.replay_data
        return replay
        
class Cell:
    def __init__(self, loc, owner, spawn_turn=None):
        self.loc = loc
        self.owner = owner
        self.spawn_turn = spawn_turn

    def __str__(self):
        return '(%s, %s, %s)' % (self.loc, self.owner, self.spawn_turn)
