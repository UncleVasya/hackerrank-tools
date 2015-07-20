#!/usr/bin/env python
#

"""
// This sample bot makes a random valid move
"""

import random
from LightOutGame import LightsOutGame

def do_turn(state):
    loc = random.choice(state.on_cells)
    state.issue_order(loc)


def main():
    map_data = ''
    line = raw_input()
    while line:
        map_data += line + '\n'
        try:
            line = raw_input()
        except: 
            break  # end of input
    
    state = LightsOutGame(map_data)
    do_turn(state)
      
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
