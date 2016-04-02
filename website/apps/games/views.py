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

        queryset = queryset.annotate(
            bot_count=Count('bot'),
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(GameList, self).get_context_data(**kwargs)
        games = context['game_list']

        game_bots_max = max([game.bot_count for game in games])
        game_matches_max = max([game.match_set.count() for game in games])
        for game in games:
            game.leader = game.bot_set.first().player
            game.difficulty_percent = (1 - game.difficulty) * 100
            game.bots_percent = float(game.bot_count) / game_bots_max * 100
            game.matches_percent = float(game.match_set.count()) / game_matches_max * 100

        return context


class GameDetail(DetailView):
    model = Game
    slug_field = 'slug__iexact'  # case-insensitive match

    def get_object(self, queryset=None):
        game = super(GameDetail, self).get_object()

        game.bots = Bot.objects.filter(game=game)\
            .select_related('player')\
            .annotate(match_count=Count('match'))\
            .prefetch_related(
                Prefetch(
                    'opponent_set',
                    queryset=Opponent.objects.select_related('match')
                )
        )

        game.matches = Match.objects.filter(game=game)\
            .prefetch_related(
                Prefetch(
                    'opponent_set',
                    queryset=Opponent.objects.select_related('bot', 'bot__player')
                )
            )

        return game

    def get_context_data(self, **kwargs):
        context = super(GameDetail, self).get_context_data()

        game = self.object

        context.update({
            'bots_count': game.bot_set.count(),
            'leader_score': game.bot_set.first().score,
            'last_match': game.match_set.first()
        })

        return context


def calc_bots_stats(bots):
    for bot in bots:
        # count wins/draws/losses
        bot.wins = bot.draws = bot.losses = 0
        for opponent in bot.opponent_set.all():
            match = opponent.match
            if match.result == 0:
                bot.draws += 1
            elif match.result == opponent.position:
                bot.wins += 1
            else:
                bot.losses += 1

        # calc percentages
        bot.win_percent = bot.draw_percent = bot.loss_percent = 0
        match_count = bot.match_count
        if match_count:
            bot.win_percent = float(bot.wins) / match_count * 100
            bot.draw_percent = float(bot.draws) / match_count * 100
            bot.loss_percent = float(bot.losses) / match_count * 100


class GameOverview(GameDetail):
    bots_limit = 10
    matches_limit = 15

    def get_context_data(self, **kwargs):
        context = super(GameOverview, self).get_context_data()

        game = self.object
        leader_score = context['leader_score']

        # bots stats
        bots = game.bots[:self.bots_limit]
        calc_bots_stats(bots)
        for bot in bots:
            bot.score_percent = bot.score / leader_score * 100

        # matches stats
        matches = game.matches[:self.matches_limit]
        for match in matches:
            match.player, match.opponent = list(match.opponent_set.all())

            # opponents relative score (%)
            player_score = match.player.bot.score / leader_score * 100
            opponent_score = match.opponent.bot.score / leader_score * 100
            score_delta = (player_score - opponent_score) / 2
            match.player_score = 50 + score_delta
            match.opponent_score = 50 - score_delta

        context.update({
            'bot_list': bots,
            'match_list': matches,
        })

        return context


class GameBots(GameDetail):
    template_name = 'games/game_bots.html'

    def get_context_data(self, **kwargs):
        context = super(GameBots, self).get_context_data(**kwargs)

        game = self.object
        bots = game.bots
        leader_score = context['leader_score']

        calc_bots_stats(bots)
        for bot in bots:
            bot.score_percent = bot.score / leader_score * 100

        context.update({
            'bot_list': bots,
        })

        return context


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
            bot_count=Count('bot'),
            score=Sum('bot__score'),
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(PlayerList, self).get_context_data(**kwargs)

        # TODO: remove this limit when pagination is done
        context['player_list'] = context['player_list'][:100]

        players = context['player_list']

        games = Game.objects.annotate(max_score=Max('bot__score'))

        # absolute stats
        for player in players:
            player.top1 = player.top10 = 0

            for bot in player.bots:
                game = next(x for x in games if x.pk == bot.game.pk)

                if bot.rank == 1:
                    player.top1 += 1
                if bot.score >= game.max_score * Decimal(0.9):
                    player.top10 += 1  # top 10% of score for this game

        # relative stats (for graphs)
        score_max = max([player.score for player in players])
        top1_max = max([player.top1 for player in players])
        top10_max = max([player.top10 for player in players])

        players_info = players.annotate(bot_count=Count('bot'))
        bots_max = players_info.aggregate(Max('bot_count'))['bot_count__max']
        for player, player_info in zip(players, players_info):
            player.bot_count = player_info.bot_count
            player.bots_percent = float(player.bot_count) / bots_max * 100

        players_info = Player.objects.annotate(match_count=Count('bot__match'))
        matches_max = players_info.aggregate(Max('match_count'))['match_count__max']
        players_info = dict(players_info.values_list('pk', 'match_count'))
        for player in players:
            player.score_percent = Decimal(player.score) / score_max * 100
            player.top1_percent = float(player.top1) / top1_max * 100
            player.top10_percent = float(player.top10) / top10_max * 100
            player.match_count = players_info[player.pk]
            player.matches_percent = float(player.match_count) / matches_max * 100

        return context


# This view is used as a base class for other views,
# it is not used directly
class PlayerDetail(DetailView):
    model = Player
    slug_field = 'name__iexact'

    queryset = Player.objects.prefetch_related(
        Prefetch('bot_set', queryset=Bot.objects.select_related('game')))

    def __init__(self, **kwargs):
        super(PlayerDetail, self).__init__(**kwargs)
        self.bot_stats = defaultdict(lambda: defaultdict(int))

    def get_object(self, queryset=None):
        player = super(PlayerDetail, self).get_object()

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
        context = super(PlayerDetail, self).get_context_data(**kwargs)

        bot_stats = self.bot_stats

        # matches stats
        matches = self.object.matches
        for match in matches:
            # opponents info
            opponents = list(match.opponent_set.all())
            if opponents[0].bot.player == self.object:
                match.player, match.opponent = opponents
            else:
                match.player, match.opponent = opponents[::-1]  # reversed
            match.opponent_name = match.opponent.bot.player.name

            # match result
            if match.result == 0:
                match.result_text = 'Draw'
                bot_stats[match.game]['draws'] += 1
            elif match.result == match.opponent.position:
                match.result_text = 'Lost match'
                bot_stats[match.game]['losses'] += 1
            else:
                match.result_text = 'Won match'
                bot_stats[match.game]['wins'] += 1

        # total stats
        total_wins = sum(bot_stats[bot]['wins'] for bot in bot_stats)
        total_losses = sum(bot_stats[bot]['losses'] for bot in bot_stats)
        total_draws = sum(bot_stats[bot]['draws'] for bot in bot_stats)
        win_percent = 0
        if matches:
            win_percent = float(total_wins) / len(matches) * 100

        context.update({
            'match_list': matches,
            'wins': total_wins,
            'losses': total_losses,
            'draws': total_draws,
            'winrate': win_percent,
        })

        return context


def add_matches_stats(matches):
    for match in matches:
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

        # opponents stats: win chance (%)
        total_score = match.player.bot.score + match.opponent.bot.score
        match.win_chance = match.player.bot.score / total_score * 100


class PlayerOverview(PlayerDetail):
    def get_context_data(self, **kwargs):
        context = super(PlayerOverview, self).get_context_data(**kwargs)

        # matches stats
        matches = self.object.matches
        add_matches_stats(matches)

        # bots stats
        bots = self.object.bot_set.all()
        for bot in bots:
            game_bots = bot.game.bot_set.count()
            bot.rank_percent = float(bot.rank) / game_bots * 100
            bot.rank_percent = 100 - bot.rank_percent

            bot.difficulty_percent = (1 - bot.game.difficulty) * 100

            stats = self.bot_stats[bot.game]
            match_count = bot.match_set.count()

            bot.wins = stats['wins']
            bot.draws = stats['draws']
            bot.losses = stats['losses']

            bot.win_percent = bot.draw_percent = bot.loss_percent = 0
            if match_count:
                bot.win_percent = float(bot.wins) / match_count * 100
                bot.draw_percent = float(bot.draws) / match_count * 100
                bot.loss_percent = float(bot.losses) / match_count * 100

        context.update({
            'bot_list': sorted(bots, key=lambda bot: -bot.rank_percent),
            'match_list': matches,
        })

        return context


class PlayerBots(PlayerDetail):
    template_name = 'games/player_bots.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerBots, self).get_context_data(**kwargs)

        bots = self.object.bot_set.all()
        for bot in bots:
            game_bots = bot.game.bot_set.count()
            bot.rank_percent = float(bot.rank) / game_bots * 100
            bot.rank_percent = 100 - bot.rank_percent

            leader_score = bot.game.bot_set.first().score
            bot.score_percent = bot.score / leader_score * 100

            stats = self.bot_stats[bot.game]
            match_count = bot.match_set.count()

            bot.win_percent = 0
            if match_count:
                bot.win_percent = float(stats['wins']) / match_count * 100

        context.update({
            'bot_list': sorted(bots, key=lambda bot: -bot.rank_percent),
        })

        return context


class PlayerBotsActive(PlayerDetail):
    template_name = 'games/player_bots_active.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerBotsActive, self).get_context_data(**kwargs)

        bots = self.object.bot_set.all()
        matches_max = max([bot.opponent_set.count() for bot in bots])
        for bot in bots:
            match_count = bot.match_set.count()
            bot.matches_percent = float(match_count) / matches_max * 100

            stats = self.bot_stats[bot.game]

            bot.wins = stats['wins']
            bot.draws = stats['draws']
            bot.losses = stats['losses']

            bot.win_percent = bot.draw_percent = bot.loss_percent = 0
            if match_count:
                bot.win_percent = float(bot.wins) / match_count * 100
                bot.draw_percent = float(bot.draws) / match_count * 100
                bot.loss_percent = float(bot.losses) / match_count * 100

        context.update({
            'bot_list': sorted(bots, key=lambda bot: -bot.matches_percent),
        })

        return context


class PlayerBotsChallenging(PlayerDetail):
    template_name = 'games/player_bots_challenging.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerBotsChallenging, self).get_context_data(**kwargs)

        # bots stats
        bots = self.object.bot_set.all()
        game_bots_max = max([bot.game.bot_set.count() for bot in bots])
        for bot in bots:
            game_bots = bot.game.bot_set.count()
            bot.game_bots_percent = float(game_bots) / game_bots_max * 100

            bot.difficulty_percent = (1 - bot.game.difficulty) * 100

            bot.rank_percent = float(bot.rank) / game_bots * 100
            bot.rank_percent = 100 - bot.rank_percent

        context.update({
            'bot_list': sorted(bots, key=lambda bot: -bot.difficulty_percent),
        })

        return context


class PlayerMatches(PlayerDetail):
    template_name = 'games/player_matches.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerMatches, self).get_context_data(**kwargs)

        matches = self.object.matches
        add_matches_stats(matches)

        context.update({
            'match_list': matches,
        })

        return context


class MatchList(ListView):
    model = Match
    ordering = ['-date']

    def get_queryset(self):
        queryset = super(MatchList, self).get_queryset()

        queryset = queryset.prefetch_related(
            Prefetch(
                'opponent_set',
                queryset=Opponent.objects.select_related('bot', 'bot__player')
            )
        ).prefetch_related(
            Prefetch(
                'game',
                queryset=Game.objects.prefetch_related('bot_set')
            )
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(MatchList, self).get_context_data(**kwargs)

        matches = context['match_list']
        for match in matches:
            match.player, match.opponent = list(match.opponent_set.all())
        add_matches_stats(matches)

        return context


class MatchDetail(DetailView):
    slug_field = 'hk_id'

    queryset = Match.objects.select_related(
        'game'
    ).prefetch_related(
        Prefetch(
            'opponent_set',
            queryset=Opponent.objects.select_related('bot', 'bot__player')
        )
    )

    def get_context_data(self, **kwargs):
        context = super(MatchDetail, self).get_context_data(**kwargs)

        match = self.object

        game_bots = match.game.bot_set.count()
        leader_score = match.game.bot_set.first().score
        for opponent in match.opponent_set.all():
            bot = opponent.bot
            bot.rank_percent = float(bot.rank) / game_bots * 100
            bot.rank_percent = 100 - bot.rank_percent
            bot.score_percent = bot.score / leader_score * 100

        return context
