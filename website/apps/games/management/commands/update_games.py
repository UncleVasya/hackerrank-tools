import requests

from django.core.management.base import BaseCommand

from apps.games.management.commands.const import API_URL
from apps.games.models import Game

URL = API_URL + 'challenges/'
API_LIMIT = 50  # hackerrank API limit for one request


class Command(BaseCommand):
    def handle(self, *args, **options):
        objects = []
        offset = 0

        while True:
            params = {
                'offset': offset,
                'limit': API_LIMIT,
            }
            r = requests.get(URL, params=params)
            data = r.json()
            objects += data['models']
            offset = len(objects)

            print 'offset: %d  total: %d' % (offset, data['total'])

            if offset >= data['total']:
                break

        # filter out non-game challenges and single player games
        objects = [x for x in objects
                   if x['kind'] == 'game' and x['player_count'] > 1]

        games_added = 0
        for game in objects:
            _, created = Game.objects.update_or_create(
                name=game['name'],
                defaults={
                    'name': game['name'],
                    'description': game['preview'],
                    'difficulty': game['difficulty_name'],
                    'slug': game['slug'],
                })
            if created:
                games_added += 1

        print 'total number of challenges: %d' % offset
        print 'number of games: %d' % len(objects)
        print 'games added: %d' % games_added
        print Game.objects.all().reverse()[:games_added].reverse()
