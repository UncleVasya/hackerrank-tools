import requests

from django.core.management.base import BaseCommand
import time

from apps.games.management.commands.const import API_URL
from apps.games.models import Game, Player, Bot

URL = API_URL + 'challenges/%game%/leaderboard'  # %game% is a game slug
API_LIMIT = 100  # max number of objects returned by hackerrank API

SLEEP_TIME = 1  # seconds between requests


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-g', '--games', nargs='*', type=str)

    def handle(self, *args, **options):
        if options['games']:
            games = Game.objects.filter(slug__in=options['games'])
        else:
            games = Game.objects.all()

        bots_parsed = bots_added = players_added = 0
        for game in games:
            print 'Parsing %s leaderboard' % game.name

            objects = get_bots_data(game)
            result = parse_bots_data(game, objects)

            bots_parsed += len(objects)
            bots_added += result['bots_added']
            players_added += result['players_added']

            print '----------------------------------'

        print 'bots parsed (total): %d' % bots_parsed
        print 'bots added (total): %d' % bots_added
        print 'players added (total): %d' % players_added


def get_bots_data(game):
    url = URL.replace('%game%', game.slug)
    objects = []
    offset = 0

    print 'url: %s' % url

    while True:
        params = {
            'offset': offset,
            'limit': API_LIMIT,
            'include_practice': 'true',
        }
        r = requests.get(url, params=params)
        data = r.json()
        objects += data['models']
        offset = len(objects)

        print 'offset: %d  total: %d' % (offset, data['total'])
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        if offset >= data['total']:
            break

    return objects


def parse_bots_data(game, objects):
    bots_added = players_added = 0

    for bot in objects:
        # bot owner
        player, created = update_player(bot)
        if created:
            players_added += 1

        # bot itself
        _, created = update_bot(bot, game, player)
        if created:
            bots_added += 1

    print 'bots added: %d' % bots_added
    print 'players added: %d' % players_added

    return {'bots_added': bots_added,
            'players_added': players_added}


def update_player(bot):
    return Player.objects.update_or_create(
        name=bot['hacker'],
        defaults={
            'country': bot['country'],
        }
    )


def update_bot(bot, game, player):
    return Bot.objects.update_or_create(
        game=game,
        player=player,
        defaults={
            'score': bot['score'],
            'language': bot['language'],
            'submitted_at': bot.get('submitted_at', 'years ago'),
        })
