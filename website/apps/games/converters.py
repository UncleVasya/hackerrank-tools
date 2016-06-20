"""
    Replay converters for different games.
    From hackerrank format to ours.
"""

import requests


def lifegame_convert(source):
    # hackerrank defaults
    rows = cols = 29
    turns_required = 80

    # get moves data from hackerrank
    moves_url = source['codechecker_stdout']
    r = requests.get(moves_url)
    moves = r.json()['payload']

    # parse moves data
    cells = []
    turns = 0
    for move in moves:
        try:
            row, col = move.split()
            cells.append([int(row), int(col), turns + 1, turns % 2])
            turns += 1
        except ValueError:
            break

    # replay template
    # TODO: only replaydata is changing between games
    replay = {
        'playernames': [x['hacker_username'] for x in source['actors']],
        'status': ['survived', 'survived'],
        'replayformat': 'json',
        'challenge': 'lifegame',
        'replaydata': {
            'cells': cells,
            'revision': 1,
            'players': 2,
            # empty map
            'map': {
                'rows': rows,
                'cols': cols,
                'data': ['-' * cols for _ in range(rows)]
            },
        },
    }

    if turns < turns_required:
        bot = turns % 2  # this bot crashed or timed out
        status = source['message'].split('\n')[0]
        replay['status'][bot] = status

    if turns % 2:
        # last move was made by first player
        replay['playerturns'] = [turns, turns-1]
    else:
        # last move was made by second player
        replay['playerturns'] = [turns-1, turns]

    return replay
