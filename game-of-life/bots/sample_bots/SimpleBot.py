#!/usr/bin/env python
#

"""
// This sample bot makes a move on the first empty cell it founds 
"""

from LifeGame import LifeGame

def doTurn(state):
    for row in range(state.height):
        for col in range(state.width):
            loc = row, col
            if state.isEmpty(loc):
                state.issueOrder(loc)
                return
    
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
