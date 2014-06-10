#!/usr/bin/env python
#

"""
// The DoTurn function is where your code goes. The PlanetWars object contains
// the state of the game, including information about all planets and fleets
// that currently exist. Inside this function, you issue orders using the
// pw.IssueOrder() function. For example, to send 10 ships from planet 3 to
// planet 8, you would say pw.IssueOrder(3, 8, 10).
//
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own. Check out the tutorials and articles on the contest website at
// http://www.ai-contest.com/resources.
"""

from LifeGame import LifeGame

def doTurn(state):
    for row_num, row in enumerate(state._map):
        for col_num, cell in enumerate(row):
            if cell == '-':
                state.issueOrder((lambda: row_num if state._my_char == 'w' else row_num+10)(), 
                                 col_num)
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
