from decimal import Decimal
from django.db.models import Prefetch, Max, Count, Sum, Case, When
from django.views.generic import ListView, DetailView
from apps.games.models import Game, Player, Bot


class GameList(ListView):
    model = Game
    ordering = ['-bot_count']  # see annotates below

    def get_queryset(self):
        queryset = super(GameList, self).get_queryset()

        # data prefetch greatly reduces number of DB queries
        # (from 60 to 4 for this view)
        queryset = queryset.prefetch_related(
            Prefetch(
                'bot_set',
                queryset=Bot.objects.select_related('player'),
                to_attr='bots',
            )
        ).annotate(
            max_score=Max('bot__score'),
            bot_count=Count('bot'),
        )

        for game in queryset:
            game.leader = next(bot for bot in game.bots
                               if bot.score == game.max_score)

        return queryset


class GameDetail(DetailView):
    slug_field = 'slug__iexact'  # case-insensitive match

    queryset = Game.objects.prefetch_related(  # optimized query
        Prefetch('bot_set', queryset=Bot.objects.select_related('player')))


class PlayerList(ListView):
    model = Player
    ordering = ['-score']  # see annotates below

    def get_queryset(self):
        queryset = super(PlayerList, self).get_queryset()

        # data prefetch greatly reduces number of DB queries
        queryset = queryset.prefetch_related(
            Prefetch(
                'bot_set',
                queryset=Bot.objects.select_related('game'),
                to_attr='bots'
            )
        ).annotate(
            score=Sum('bot__score'),
            bot_count=Count('bot'),
        )

        games = Game.objects.annotate(max_score=Max('bot__score'))

        for player in queryset:
            player.top1 = player.top10 = 0

            for bot in player.bots:
                game = next(x for x in games if x.pk == bot.game.pk)

                if bot.score == game.max_score:
                    player.top1 += 1
                if bot.score >= game.max_score * Decimal(0.9):
                    player.top10 += 1  # top 10% of score for this game

        return queryset


class PlayerDetail(DetailView):
    slug_field = 'name__iexact'

    queryset = Player.objects.prefetch_related(
        Prefetch('bot_set', queryset=Bot.objects.select_related('game')))
