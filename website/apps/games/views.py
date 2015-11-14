from collections import defaultdict
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
        ).select_related('game').prefetch_related('game__bot_set')

        return player

    def get_context_data(self, **kwargs):
        context = super(PlayerOverview, self).get_context_data(**kwargs)

        wins = losses = draws = 0  # totals for this player
        bot_results = defaultdict(lambda: defaultdict(int))

        matches = self.object.matches
        for match in matches:
            # opponents info
            opponents = list(match.opponent_set.all())
            if opponents[0].bot.player == self.object:
                match.player, match.opponent = opponents
            else:
                match.player, match.opponent = opponents[::-1]  # reversed
            match.opponent_name = match.opponent.bot.player.name

            # opponents stats: relative rank (%)
            game_bots = match.game.bot_set.count()
            player_rank = float(match.player.bot.rank) / game_bots * 100
            opponent_rank = float(match.opponent.bot.rank) / game_bots * 100
            rank_delta = (player_rank - opponent_rank) / 2
            match.player_rank = 50 - rank_delta
            match.opponent_rank = 50 + rank_delta

            # opponents stats: relative score (%)
            leader_score = match.game.bot_set.first().score
            player_score = match.player.bot.score / leader_score * 100
            opponent_score = match.opponent.bot.score / leader_score * 100
            score_delta = (player_score - opponent_score) / 2
            match.player_score = 50 + score_delta
            match.opponent_score = 50 - score_delta

            # opponents stats: relative score (%)
            total_score = match.player.bot.score + match.opponent.bot.score
            match.win_chance = match.player.bot.score / total_score * 100

            # match result
            if match.result == 0:
                match.result_text = 'Draw'
                bot_results[match.game]['draws'] += 1
                draws += 1
            elif match.result == match.opponent.position:
                match.result_text = 'Lost match'
                bot_results[match.game]['losses'] += 1
                losses += 1
            else:
                match.result_text = 'Won match'
                bot_results[match.game]['wins'] += 1
                wins += 1

        # bots stats
        bots = self.object.bot_set.all()
        for bot in bots:
            game_bots = bot.game.bot_set.count()
            bot.rank_percent = float(bot.rank) / game_bots * 100
            bot.rank_percent = 100 - bot.rank_percent

            bot.difficulty_percent = (1 - bot.game.difficulty) * 100

            results = bot_results[bot.game]
            match_count = bot.match_set.count()

            bot.wins = results['wins']
            bot.draws = results['draws']
            bot.losses = results['losses']

            bot.win_percent = bot.draw_percent = bot.loss_percent = 0
            if match_count:
                bot.win_percent = float(bot.wins) / match_count * 100
                bot.draw_percent = float(bot.draws) / match_count * 100
                bot.loss_percent = float(bot.losses) / match_count * 100

        winrate = 0
        if matches:
            winrate = float(wins) / len(matches) * 100

        context.update({
            'bot_list': sorted(bots, key=lambda bot: -bot.rank_percent),
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
