from decimal import Decimal
from django.db.models import Prefetch, Max, Count, Sum, Case, When
from django.views.generic import ListView, DetailView
from apps.games.models import Game, Player, Bot, Match, Opponent


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


class PlayerOverview(DetailView):
    model = Player
    slug_field = 'name__iexact'
    template_name = 'games/player_overview.html'

    queryset = Player.objects.prefetch_related(
        Prefetch('bot_set', queryset=Bot.objects.select_related('game')))

    def get_object(self, queryset=None):
        player = super(PlayerOverview, self).get_object()

        player.matches = Match.objects.filter(
            bots__player=player
        ).prefetch_related(
            Prefetch(
                'opponent_set',
                queryset=Opponent.objects.select_related('bot', 'bot__player')
            )
        ).select_related('game')

        return player

    def get_context_data(self, **kwargs):
        context = super(PlayerOverview, self).get_context_data(**kwargs)

        matches = self.object.matches

        wins = losses = draws = winrate = 0
        for match in matches:
            opponents = list(match.opponent_set.all())
            if opponents[0].bot.player == self.object:
                match.opponent = opponents[1]
            else:
                match.opponent = opponents[0]
            match.opponent_name = match.opponent.bot.player.name

            if match.result == 0:
                match.result_text = 'Draw'
                draws += 1
            elif match.result == match.opponent.position:
                match.result_text = 'Lost match'
                losses += 1
            else:
                match.result_text = 'Won match'
                wins += 1

        if matches:
            winrate = float(wins) / len(matches) * 100

        context.update({
            'match_list': matches,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'winrate': winrate,
        })

        return context


class MatchList(ListView):
    model = Match
    ordering = ['-date']

    def get_queryset(self):
        queryset = super(MatchList, self).get_queryset()

        queryset = queryset.select_related('game').prefetch_related(
            Prefetch(
                'bots',
                queryset=Bot.objects.select_related('player'),
            )
        )

        return queryset


class MatchDetail(DetailView):
    slug_field = 'hk_id'

    queryset = Match.objects.select_related(
        'game'
    ).prefetch_related(
        Prefetch(
            'bots',
            queryset=Bot.objects.select_related('player')
        )
    )
