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
  while(True):
    current_line = raw_input()
    if len(current_line) >= 5 and current_line.startswith("ready"):
        LifeGame.finishTurn()
    elif len(current_line) >= 2 and current_line.startswith("go"):
      state = LifeGame(map_data)
      doTurn(state)
      state.finishTurn()
      map_data = ''
    else:
      map_data += current_line + '\n'


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
