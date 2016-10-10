import datetime
from django.core import management
from django.db.models import Count
import requests

from django.core.management.base import BaseCommand
import time
from apps.games.converters import convert_replay

from apps.games.management.commands.const import API_URL, HACKERRANK_URL
from apps.games.models import Game, Match, ParsingInfo, Bot, Opponent

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

FORWARD = 1
BACKWARDS = -1

SLEEP_TIME = 1  # seconds between requests

parsing = ParsingInfo.get_solo()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-l', '--limit',
                            nargs='?', type=int, default=100, const=100)
        parser.add_argument('-b', '--backwards',
                            nargs='?', type=bool, default=False, const=False)
        parser.add_argument('-f', '--fails_limit',
                            nargs='?', type=int, default=5, const=5)

    def handle(self, *args, **options):
        latest_match = parsing.newest_parsed_match
        if latest_match:
            if options['backwards']:
                start = parsing.oldest_parsed_match - 1
                direction = BACKWARDS

            else:
                start = latest_match + 1
                direction = FORWARD
            matches = get_matches(start, options['limit'],
                                  options['fails_limit'], direction)
        else:
            print '-----------------------'
            print 'No parsed data in DB yet.'
            print 'Searching for latest match on hackerrank.com'
            print '-----------------------'
            latest_match = find_latest_match()

            parsing.newest_parsed_match = latest_match
            parsing.oldest_parsed_match = latest_match
            parsing.save()

            matches = get_matches(latest_match, options['limit'],
                                  options['fails_limit'], BACKWARDS)

        print 'SAVING MATCHES'
        print '-----------------------'

        for match in matches:
            parse_match(match)

        print '-----------------------'
        print 'DONE'
        print '%d matches was saved or updated in DB' % len(matches)
        print '-----------------------'


def get_matches(match_id, limit=100, fails_limit=5, direction=FORWARD):
    print '-----------------------'
    print 'GETTING %d MATCHES' % limit
    print 'direction: %d' % direction
    print 'fails limit: %s' % fails_limit
    print '-----------------------'

    objects = []
    checked = failures = 0
    while checked < limit and failures < fails_limit:
        print 'id: %d    ' % match_id,

        r = requests.get(URL.replace('%id%', str(match_id)))
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        try:
            data = r.json()['model']
        except:
            print '[NOT FOUND]'
            failures += 1
            print 'Failures: %d/%d' % (failures, fails_limit)
            continue
        finally:
            match_id += direction
            checked += 1

        # match parsed successfully
        failures = 0
        if direction == FORWARD:
            parsing.newest_parsed_match = match_id
        else:
            parsing.oldest_parsed_match = match_id

        # some output to the user
        print '%s     ' % data['challenge_slug'],
        if Game.objects.filter(slug=data['challenge_slug']).exists():
            objects.append(data)
            print '[ADDED]'
        else:
            print '[SKIPPED]'

        if checked % 10 == 0:
            print '-----------------------'
            print 'checked: %d   added: %d' % (checked, len(objects))
            print '-----------------------'

    parsing.save()

    return objects


def fix_broken_matches(game):
    print '-----------------------'
    print 'GETTING MATCHES WITH MISSING BOTS'
    print 'Game: %s' % game
    print '-----------------------'

    matches = get_broken_matches(game)

    broken_num = matches.count()
    print ' matches to fix: %d' % broken_num
    # matches = matches[:100]
    # print ' fixing this time: %d' % matches.count()
    print '-----------------------'

    objects = []
    for match in matches:
        print 'id: %d     %s' % (match.hk_id, match.game)

        r = requests.get(URL.replace('%id%', str(match.hk_id)))
        time.sleep(SLEEP_TIME)  # let's be gentle with hackerrank.com

        try:
            data = r.json()['model']
            objects.append(data)
        except ValueError:
            match.delete()  # looks like match data is gone from hackerrank

        if len(objects) % 10 == 0:
            print '-----------------------'
            print 'matches added: %d' % len(objects)
            print '-----------------------'

    print '-----------------------'

    for match in objects:
        parse_match(match)

    # matches that are still broken can not be fixed
    unfixed = get_broken_matches(game)
    unfixed_num = unfixed.count()
    unfixed.delete()

    print '-----------------------'
    print 'DONE FIXING MATCHES'
    print 'Game: %s' % game
    print '-----------------------'
    print ' fixed:   %5d' % (broken_num - unfixed_num)
    print ' deleted: %5d' % unfixed_num


def get_broken_matches(game):
    matches = Match.objects.filter(game__slug=game)

    # matches with less than 2 bots
    matches = matches.annotate(
        bots_num=Count('bots')
    ).filter(bots_num__lt=2)

    return matches


def parse_match(data):
    try:
        match, _ = Match.objects.update_or_create(
            hk_id=data['id'],
            defaults={
                'game': Game.objects.get(slug=data['challenge_slug']),
                'result': data['result'],
                'message': data['message'],
                'date': datetime.datetime.fromtimestamp(int(data['updated_at'])),
                'replay': convert_replay(data),
            }
        )
    except Exception as e:
        print 'id: %d' % data['id']
        print 'Failed to parse.\n%s' % e
        print '------------------------'
        return

    match.bots.clear()
    for bot_data in data['actors']:
        try:
            bot = Bot.objects.get(
                game=match.game,
                player__name=bot_data['hacker_username'],
            )
            Opponent(
                match=match,
                bot=bot,
                position=bot_data['actor']
            ).save()
        except Exception as e:
            print 'id: %d' % data['id']
            print 'WARNING: Can not add bot to match'
            print 'game: %s  player: %s' % (match.game, bot_data['hacker_username'])
            print 'exception: %s' % e
            print '-----------------------'
            print 'Updating bots for this game'

            match.bots.clear()

            break


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
