#!/usr/bin/env python
#

from sys import stdout

OFF = '0'
ON = '1'


class LightsOutGame:
    def __init__(self, map_data):
        self.player = None
        self.height = None
        self.width = None
        self.map = []
        self.on_cells = []
        self.off_cells = []

        self.parse_game_state(map_data)

    def is_on(self, (row, col)):
        return self.map[row][col] == ON

    def in_bounds(self, (row, col)):
        return 0 <= row < self.height and 0 <= col < self.width

    @staticmethod
    def issue_order((row, col)):
        stdout.write("%d %d \n" % (row, col))
        stdout.flush()

    def parse_game_state(self, s):
        lines = s.split("\n")

        for line in lines:
            # check if we got player char
            if len(line) == 1:
                if line[0] in ['1', '2']:
                    self.player = line[0]

            # check if we got map line
            elif len(line) > 1 and line[0] in ['0', '1']:
                self.map.append(list(line))

        self.height = len(self.map)
        self.width = len(self.map[0])

        # fill info about living cells
        for row in range(self.height):
            for col in range(self.width):
                loc = (row, col)
                cell = self.map[row][col]
                if cell == ON:
                    self.on_cells.append(loc)
                else:
                    self.off_cells.append(loc)

        return 1
