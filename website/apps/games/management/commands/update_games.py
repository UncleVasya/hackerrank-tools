from collections import defaultdict
import json
from django.core.management.base import BaseCommand

import requests
from apps.games.models import Game

CHALLENGES_URL = 'https://www.hackerrank.com/rest/contests/master/challenges'
API_LIMIT = 50  # max number of objects returned by hackerrank API


class Command(BaseCommand):
    def handle(self, *args, **options):
        objects = []
        offset = 0

        while True:
            r = requests.get(CHALLENGES_URL,
                             params={'offset': offset, 'limit': API_LIMIT})
            data = r.json()
            objects += data['models']
            offset = len(objects)

            print 'offset: %d  total: %d' % (offset, data['total'])

            if offset >= data['total']:
                break

        objects = [x for x in objects
                   if x['kind'] == 'game' and x['player_count'] > 1]

        games_added = 0
        for x in objects:
            if not Game.objects.filter(hk_id=x['id']).exists():
                Game(
                    name=x['name'],
                    description=x['preview'],
                    difficulty=x['difficulty_name'],
                    hk_id=x['id'],
                    hk_json=x
                ).save()
                games_added += 1

        games_num_by_player_num = defaultdict(int)
        for game in objects:
            players = game['player_count']
            games_num_by_player_num[players] += 1

        print 'total number of challenges: %d' % offset
        print 'number of games: %d' % len(objects)
        print 'by players count: %s' % games_num_by_player_num
        print 'games added: %d' % games_added
        print Game.objects.all().reverse()[:games_added].reverse()
