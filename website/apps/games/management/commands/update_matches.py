import datetime
import requests

from django.core.management.base import BaseCommand
import time

from apps.games.management.commands.const import API_URL, HACKERRANK_URL
from apps.games.models import Game, Match, ParsingInfo, Bot

URL = API_URL + 'games/%id%'

#
# As of October 2015, number of Matches on hackerrank.com
# is somewhere between these values.
#
# They are used only on initial DB filling, to help find latest Matches.
#
# If these bounds are no longer correct, it is OK:
# script will check them and adjust if needed
#
LOWER_BOUND = 5000000
UPPER_BOUND = 6000000

SLEEP_TIME = 1  # seconds between requests

parsing = ParsingInfo.get_solo()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-l', '--limit',
                            nargs='?', type=int, default=100)
        parser.add_argument('-b', '--backwards',
                            nargs='?', type=bool, default=False)

    def handle(self, *args, **options):
        latest_match = parsing.newest_parsed_match
        if latest_match:
            if options['backwards']:
                matches = get_old_matches(parsing.oldest_parsed_match - 1,
                                          options['limit'])
            else:
                matches = get_new_matches(latest_match + 1,
                                          options['limit'])
        else:
            print '-----------------------'
            print 'No parsed data in DB yet.'
            print 'Searching for latest match on hackerrank.com'
            print '-----------------------'
            latest_match = find_latest_match()

            parsing.newest_parsed_match = latest_match
            parsing.oldest_parsed_match = latest_match
            parsing.save()

            matches = get_old_matches(latest_match, options['limit'])

        print 'SAVING MATCHES'
        print '-----------------------'

        for match in matches:
            parse_match(match)

        print '-----------------------'
        print 'DONE'
        print '%d matches was saved or updated in DB' % len(matches)
        print '-----------------------'


def get_new_matches(match_id, limit=100):
    print '-----------------------'
    print 'GETTING NEW MATCHES'
    print '-----------------------'

    objects = []
    while len(objects) < limit:
        print 'id: %d...    ' % match_id,

        r = requests.get(URL.replace('%id%', str(match_id)))
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        try:
            data = r.json()['model']

            print '%s     ' % data['challenge_slug'],
            if Game.objects.filter(slug=data['challenge_slug']).exists():
                objects.append(data)
                print '[ADDED]'

                if len(objects) % 10 == 0:
                    print '-----------------------'
                    print 'matches added: %d' % len(objects)
                    print '-----------------------'
            else:
                print '[SKIPPED]'
        except:
            break  # no more Matches
        finally:
            parsing.newest_parsed_match = match_id
            match_id += 1

    parsing.save()

    return objects


def get_old_matches(match_id, limit=100):
    print '-----------------------'
    print 'GETTING %d OLDER MATCHES' % limit
    print '-----------------------'
    print ' start id: %d \n limit: %d' % (match_id, limit)
    print '-----------------------'

    objects = []
    while len(objects) < limit and match_id >= 0:
        print 'id: %d...    ' % match_id,

        r = requests.get(URL.replace('%id%', str(match_id)))
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        try:
            data = r.json()['model']

            print '%s     ' % data['challenge_slug'],

            if Game.objects.filter(slug=data['challenge_slug']).exists():
                objects.append(data)
                print '[ADDED]'

                if len(objects) % 10 == 0:
                    print '-----------------------'
                    print 'matches added: %d' % len(objects)
                    print '-----------------------'
            else:
                print '[SKIPPED]'
        except:
            print '[NOT FOUND]'

        parsing.oldest_parsed_match = match_id + 1
        match_id -= 1

    parsing.save()

    return objects


def parse_match(data):
    print 'id: %d' % data['id']

    match, _ = Match.objects.update_or_create(
        hk_id=data['id'],
        defaults={
            'game': Game.objects.get(slug=data['challenge_slug']),
            'result': data['result'],
            'message': data['message'],
            'date': datetime.datetime.fromtimestamp(int(data['updated_at']))
        }
    )

    match.bots.clear()
    for bot_data in data['actors']:
        try:
            match.bots.add(Bot.objects.get(
                game=match.game,
                player__name=bot_data['hacker_username'],
            ))
        except Exception as e:
            print 'WARNING: Can not add bot to match'
            print 'game: %s  player: %s' % (match.game, bot_data['hacker_username'])
            print 'exception: %s' % e
            print '-----------------------'
            print 'You can fix this with update_bots command.'
            print '-----------------------'


def find_latest_match():
    lower, upper = adjust_bounds(LOWER_BOUND, UPPER_BOUND)

    print 'FINDING LATEST MATCH'
    print '-----------------------'

    while upper - lower > 1:
        match_id = (lower + upper) / 2
        print ' lower: %d \n upper: %d \n check: %d' % \
              (lower, upper, match_id),

        r = requests.get(URL.replace('%id%', str(match_id)))
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        try:
            r.json()
            print '[FOUND]'
            lower = match_id
        except:
            print '[NOT FOUND]'
            upper = match_id
        print '-----------------------'

    latest_match = upper - 1

    print 'Latest match: %d' % latest_match
    print URL.replace('%id%', str(latest_match))
    print HACKERRANK_URL + 'showgame/%d' % latest_match
    print '-----------------------'

    return latest_match


def adjust_bounds(lower, upper):
    print 'ADJUSTING SEARCH BOUNDS'
    print '-----------------------'
    print 'Initial bounds: (%d, %d)' % (lower, upper)
    print '-----------------------'

    # just in case somebody uses this function with lower > upper
    # (what is meaningless)
    upper = max(upper, lower)

    print 'Adjusting lower bound...'

    # lower bound is ok if there is a Match for it;
    # otherwise decrease lower bound until Match is found
    while lower > 0:
        print 'Checking %d...    ' % lower,

        r = requests.get(URL.replace('%id%', str(lower)))
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        try:
            r.json()
            print '[OK]'
            break
        except:
            print '[NOT OK]'
            lower /= 2

    print '---------------------'
    print 'Adjusting upper bound...'

    # upper bound is ok if there is no Match for it;
    # otherwise increase upper bound as long as Match is found
    while True:
        print 'Checking %d...    ' % upper,

        r = requests.get(URL.replace('%id%', str(upper)))
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        try:
            r.json()
            print '[NOT OK]'
            upper *= 2
        except:
            print '[OK]'
            break

    print '---------------------'
    print 'Adjusted bounds: (%d, %d)' % (lower, upper)
    print '-----------------------'

    return lower, upper
