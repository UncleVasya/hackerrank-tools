from django.core.management.base import BaseCommand
from apps.games.models import Game


class Command(BaseCommand):
    def handle(self, *args, **options):
        # games = Game.objects.filter(
        #     pk__in=Game.objects.all().values_list('pk')[:5]
        # )
        # print games
        # games.delete()
        #
        # game = Game.objects.last()
        # print game
        # game.delete()

        Game.objects.all().delete()

