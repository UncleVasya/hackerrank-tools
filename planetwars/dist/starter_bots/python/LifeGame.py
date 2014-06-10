#!/usr/bin/env python
#

from math import ceil, sqrt
from sys import stdout

# class Cell:
    # def __init__(self, loc, owner, spawn_turn=None):
        # self.loc = loc
        # self.owner = owner

class LifeGame:
  def __init__(self, gameState):
    self.parseGameState(gameState)

  # def getMap(self):
    # return self._map
    
  # def getMyChar(self):
    # return self._my_char

  def issueOrder(self, row, col):
    stdout.write("%d %d \n" % (row, col))
    stdout.flush()

  def parseGameState(self, s):
    self._my_char = ''
    self._map = []
    lines = s.split("\n")

    for line in lines:
      # check if we got player char
      if len(line) == 1:
        if line[0] in ['w', 'b']:
            self._my_char = line[0]
      # check if we got game map
      elif len(line) > 1 and line[0] in ['w', 'b', '-']:
        self._map.append(list(line))
    
    return 1

  @staticmethod
  def finishTurn():
    stdout.write("go\n")
    stdout.flush()
