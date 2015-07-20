#!/usr/bin/env python
#

"""
// This sample bot makes a move on the first empty cell it founds 
"""

from LightOutGame import LightsOutGame

def do_turn(state):
    for row in range(state.height):
        for col in range(state.width):
            loc = row, col
            if state.is_on(loc):
                state.issue_order(loc)
                return


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
