#!/usr/bin/env python2

from random import randrange, choice, shuffle, randint, seed, random
from collections import defaultdict

import operator
from game import Game

try:
    from sys import maxint
except ImportError:
    from sys import maxsize as maxint

OFF = 0
ON = 1


class LightsOut(Game):
    def __init__(self, options=None):
        # setup options
        map_text = options['map']
        self.turns = int(options['turns'])
        self.sim_steps = int(options['sim_steps'])
        self.loadtime = int(options['loadtime'])
        self.turntime = int(options['turntime'])
        self.engine_seed = options.get('engine_seed', randint(-maxint - 1, maxint))
        self.player_seed = options.get('player_seed', randint(-maxint - 1, maxint))
        seed(self.engine_seed)

        self.cutoff_percent = options.get('cutoff_percent', 0.85)
        self.cutoff_turn = options.get('cutoff_turn', 150)

        self.scenario = options.get('scenario', False)

        map_data = self.parse_map(map_text)

        self.turn = 0
        self.num_players = map_data["num_players"]
        self.changes = []

        self.player_to_begin = 0
        # used to cutoff games early
        self.cutoff = None
        self.cutoff_bot = None  # Can be ant owner, FOOD or LAND
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
        self.map = [[OFF] * self.width for _ in range(self.height)]

        # initialize ON cells
        for row, col in map_data['on_cells']:
            self.map[row][col] = ON

        # original map to put in a replay data
        self.original_map = []
        for map_row in self.map:
            self.original_map.append(map_row[:])

        # initialize scores
        self.score = [0] * self.num_players
        self.bonus = [0] * self.num_players
        self.score_history = [[s] for s in self.score]

        # cache used by neighbourhood_offsets() to determine nearby squares
        self.offsets_cache = {}

        # used to track dead players
        self.killed = [False for _ in range(self.num_players)]

        # the engine may kill players before the game starts and this is needed
        # to prevent errors
        self.orders = [[] for i in range(self.num_players)]

    def parse_map(self, map_text):
        """ Parse the map_text into a more friendly data structure """
        width = height = None
        row = 0
        num_players = None
        cell_states = [ON, OFF]
        on_cells = []

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
                if num_players is None:
                    raise Exception("map",
                                    "players count expected before map lines")
                if len(value) != width:
                    raise Exception("map",
                                    "Incorrect number of cols in row %s. "
                                    "Got %s, expected %s."
                                    % (row, len(value), width))
                for col, c in enumerate(value):
                    if int(c) == ON:
                        on_cells.append((row, col))
                    elif int(c) not in cell_states:
                        raise Exception("map",
                                        "Invalid character in map: %s" % c)
                row += 1
        if height != row:
            raise Exception("map",
                            "Incorrect number of rows.  Expected %s, got %s"
                            % (height, row))
        return {
            'size': (height, width),
            'num_players': num_players,
            'on_cells': on_cells
        }

    def get_map_output(self):
        result = []
        for row in self.original_map:
            result.append(''.join([str(cell) for cell in row]))
        return result

    def parse_orders(self, player, lines):
        """ Parse orders from the given player

            Orders must be of the form: row col
            row, col must be integers
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
            Cell state must be ON
        """
        valid = []
        valid_orders = []
        for line, (row, col) in zip(lines, orders):
            if row < 0 or row >= self.height or col < 0 or col >= self.width:
                invalid.append((line, 'out of bounds'))
                continue
            if self.map[row][col] != ON:
                invalid.append((line, 'cell state must be ON'))
                continue

            # this order is valid!
            valid_orders.append((row, col))
            valid.append(line)

        return valid_orders, valid, ignored, invalid

    def is_his_turn(self, player):
        """ Used to determine if player has right to make moves this turn
        """
        return (self.turn + 1) % 2 == player

    def do_orders(self):
        """ Execute player orders and handle conflicts
        """
        for player in range(self.num_players):
            if self.is_alive(player) and self.is_his_turn(player):
                for loc in self.orders[player]:
                    row, col = loc
                    self.flip(row, col)
                    self.flip(row, col+1)
                    self.flip(row+1, col)

    def flip(self, row, col):
        """ Changes state of the cell (ON/OFF) and records the change.
            If location is out of range, does nothing.
        """
        if 0 <= row < self.height and 0 <= col < self.width:
            self.map[row][col] = int(not self.map[row][col])
            self.changes.append(Change((row, col), self.turn))

    def remaining_players(self):
        """ Return the players still alive """
        return [p for p in range(self.num_players) if self.is_alive(p)]

    # # Common functions for all games

    def is_rank_stabilized(self):
        """ For this game rank is stabilized if someone won the game
            (if there are no ON cells left)
        """
        return not any(ON in row for row in self.map)

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
        elif self.is_rank_stabilized():
            self.cutoff = 'rank stabilized'
            return True
        else:
            return False

    def kill_player(self, player):
        """ Used by engine to signal that a player is out of the game """
        self.killed[player] = True

    def start_game(self):
        """ Called by engine at the start of the game """
        self.game_started = True

    def finish_game(self):
        """ Called by engine at the end of the game """
        if self.cutoff is None:
            # game ended normally
            self.cutoff = 'turn limit reached'
        elif self.cutoff == 'rank stabilized':
            winner = (self.turn + 1) % 2  # bot who made last move
            self.score[winner] = 100
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
        player_chars = '12'
        # first row contains character of the player 
        message = player_chars[player] + '\n'
        # here goes game grid
        message += '\n'.join(''.join(str(cell) for cell in row) for row in self.map)
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

        # changes data
        changes = [[change.loc[0], change.loc[1], change.turn]
                 for change in self.changes]
        replay['changes'] = sorted(changes, key=operator.itemgetter(2))

        # scores
        replay['scores'] = self.score_history
        replay['bonus'] = self.bonus
        replay['winning_turn'] = self.winning_turn
        replay['ranking_turn'] = self.ranking_turn
        replay['cutoff'] = self.cutoff

        return replay


class Change:
    def __init__(self, loc, turn):
        self.loc = loc
        self.turn = turn

    def __str__(self):
        return '(%s, %s)' % (self.loc, self.turn)
