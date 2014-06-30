#!/usr/bin/env python
#

from math import ceil, sqrt
from sys import stdout

EMPTY = '-'

class LifeGame:
  def __init__(self, gameState):
    self.player = None
    self.height = None
    self.width = None
    self.map = []
    self.my_cells = []
    self.enemy_cells = []
    self.alive_cells = []
    
    self.parseGameState(gameState)

  def isEmpty(state, (row, col)):
    return state.map[row][col] == EMPTY
    
  def inBounds(state, (row, col)):
    return 0 <= row < state.height and \
           0 <= col < state.width
  
  def issueOrder(self, (row, col)):
    stdout.write("%d %d \n" % (row, col))
    stdout.flush()

  def parseGameState(self, s):
    lines = s.split("\n")

    for line in lines:
        # check if we got player char
        if len(line) == 1:
            if line[0] in ['w', 'b']:
                self.player = line[0]
      
        # check if we got map line
        elif len(line) > 1 and line[0] in ['w', 'b', '-']:
            self.map.append(list(line))
    
    self.height = len(self.map)
    self.width  = len(self.map[0])
    
    # fill info about living cells
    for row in range(self.height):
        for col in range(self.width):
            loc = (row, col)
            cell = self.map[row][col]
            if cell == self.player:
                self.my_cells.append(loc)
            elif cell != EMPTY:
                self.enemy_cells.append(loc)
    self.alive_cells = self.my_cells + self.enemy_cells
    
    return 1

  @staticmethod
  def finishTurn():
    stdout.write("go\n")
    stdout.flush()
