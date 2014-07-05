#!/usr/bin/env python
#

"""
// This sample bot makes a list of empty cells with at least one living neighbour.
// Then it randomly choses a cell from this list and makes a move.
// 
// If produced list is empty then game has just started. Bot randomly picks any cell 
// on the map.
"""

import random
from sys import stdout
from LifeGame import LifeGame

def getCellEmptyNeighs(state, (row, col)):
    neighs = set()
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            loc = (row + dx, col + dy)
            is_original = (loc == (row, col))
            if state.inBounds(loc) and not is_original and state.isEmpty(loc):
                neighs.add(loc)
                
    return neighs
            
def doTurn(state):
    neighs_of_alive = set();
    for loc in state.alive_cells:
        neighs_of_alive |= getCellEmptyNeighs(state, loc)
    
    loc = None
    if neighs_of_alive:
        loc = random.sample(neighs_of_alive, 1)[0]
    else: # empty board, just make random move
        loc = (random.randint(0, state.height - 1),
               random.randint(0, state.width - 1))
    
    state.issueOrder(loc)
    
def main():
    map_data = ''
    line = raw_input()
    while line:
        map_data += line + '\n'
        try:
            line = raw_input()
        except: 
            break # end of input
    
    state = LifeGame(map_data)
    doTurn(state)
    
    raw_input()


if __name__ == '__main__':
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass
  try:
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
