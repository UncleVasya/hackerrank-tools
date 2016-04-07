from collections import defaultdict
from decimal import Decimal
from django.db.models import Prefetch, Max, Count, Sum
from django.views.generic import ListView, DetailView
from pure_pagination import Paginator, PageNotAnInteger
from apps.games.models import Game, Player, Bot, Match, Opponent


class GameList(ListView):
    model = Game

    def get_context_data(self, **kwargs):
        context = super(GameList, self).get_context_data(**kwargs)
        games = context['game_list']

        # get bot counts for every game
        bot_counts = Bot.objects.values_list('game')\
            .annotate(bot_count=Count('*'))\
            .order_by()
        bot_counts = defaultdict(int, bot_counts)

        for game in games:
            game.bot_count = bot_counts[game.id]

        # get match counts for every game
        match_counts = Match.objects.all().values_list('game')\
            .annotate(match_count=Count('*'))\
            .order_by()
        match_counts = defaultdict(int, match_counts)

        for game in games:
            game.match_count = match_counts[game.id]

        leaders = Bot.objects.filter(rank=1).select_related('player')
        leaders = {bot.game_id: bot.player for bot in leaders}

        game_bots_max = max([game.bot_count for game in games])
        game_matches_max = max([game.match_count for game in games])
        for game in games:
            game.leader = leaders[game.id]
            game.difficulty_percent = (1 - game.difficulty) * 100
            game.bots_percent = float(game.bot_count) / game_bots_max * 100
            game.matches_percent = float(game.match_count) / game_matches_max * 100

        context.update({
            'game_list': sorted(games, key=lambda game: -game.bot_count),
        })

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


def calc_relative_strength(match, leader_score):
    match.player, match.opponent = list(match.opponent_set.all())

    # opponents relative score (%)
    player_score = match.player.bot.score / leader_score * 100
    opponent_score = match.opponent.bot.score / leader_score * 100
    score_delta = (player_score - opponent_score) / 2
    match.player_score = 50 + score_delta
    match.opponent_score = 50 - score_delta


class GameOverview(GameDetail):
    bots_limit = 10
    matches_limit = 15

    def get_context_data(self, **kwargs):
        context = super(GameOverview, self).get_context_data()

        game = self.object
        leader_score = game.bot_set.first().score

        # bots stats
        bots = game.bots[:self.bots_limit]
        calc_bots_stats(bots)
        for bot in bots:
            bot.score_percent = bot.score / leader_score * 100

        # matches stats
        matches = game.matches[:self.matches_limit]
        for match in matches:
            calc_relative_strength(match, leader_score)

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
        leader_score = game.bot_set.first().score

        calc_bots_stats(bots)
        for bot in bots:
            bot.score_percent = bot.score / leader_score * 100

        context.update({
            'bot_list': bots,
        })

        return context


class GameBotsActive(GameDetail):
    template_name = 'games/game_bots_active.html'

    def get_context_data(self, **kwargs):
        context = super(GameBotsActive, self).get_context_data(**kwargs)

        game = self.object
        bots = game.bots

        matches_max = game.bot_set.all() \
            .annotate(match_count=Count('match')) \
            .aggregate(Max('match_count'))['match_count__max']

        calc_bots_stats(bots)
        for bot in bots:
            bot.matches_percent = float(bot.match_count) / matches_max * 100

        context.update({
            'bot_list': sorted(bots, key=lambda bot: -bot.matches_percent),
        })

        return context


class GameMatches(GameDetail):
    template_name = 'games/game_matches.html'

    def get_context_data(self, **kwargs):
        context = super(GameMatches, self).get_context_data(**kwargs)

        game = self.object
        matches = game.matches
        leader_score = game.bot_set.first().score

        for match in matches:
            calc_relative_strength(match, leader_score)

        context.update({
            'match_list': matches,
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
                to_attr='bots'
            )
        ).annotate(
            score=Sum('bot__score'),
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(PlayerList, self).get_context_data(**kwargs)
        players = context['player_list']

        # used to check if bot is in Top 10% by score
        games = Game.objects.annotate(max_score=Max('bot__score'))

        # calc overall best results
        bots_max = Player.objects\
            .annotate(bot_count=Count('bot'))\
            .aggregate(Max('bot_count'))['bot_count__max']

        matches_max = Player.objects\
            .annotate(match_count=Count('bot__match'))\
            .aggregate(Max('match_count'))['match_count__max']

        score_max = Player.objects\
            .annotate(score=Sum('bot__score'))\
            .aggregate(Max('score'))['score__max']

        top1_max = Bot.objects.filter(rank=1).values('player_id')\
            .annotate(top1_count=Count('*'))\
            .aggregate(Max('top1_count'))['top1_count__max']

        top10_counts = defaultdict(int)
        for bot in Bot.objects.all():
            game = next(x for x in games if x.id == bot.game_id)
            if bot.score >= game.max_score * Decimal(0.9):
                top10_counts[bot.player_id] += 1  # top 10% by score on this game
        top10_max = max(top10_counts.values())

        # paginate
        page_num = self.request.GET.get('page', 1)
        page = Paginator(players, 50).page(page_num)
        players = page.object_list

        player_ids = [player.id for player in players]

        # absolute stats
        for player in players:
            player.top1 = player.top10 = 0

            for bot in player.bots:
                game = next(x for x in games if x.pk == bot.game_id)

                if bot.rank == 1:
                    player.top1 += 1
                if bot.score >= game.max_score * Decimal(0.9):
                    player.top10 += 1  # top 10% of score for this game

        bot_counts = Bot.objects.order_by()\
            .filter(player__in=player_ids)\
            .values('player')\
            .annotate(bot_count=Count('*'))\
            .values_list('player', 'bot_count')
        bot_counts = dict(bot_counts)
        for player in players:
            player.bot_count = bot_counts[player.id]
            player.bots_percent = float(player.bot_count) / bots_max * 100

        match_counts = Opponent.objects.order_by()\
            .filter(bot__player__in=player_ids)\
            .values('bot__player')\
            .annotate(match_count=Count('*'))\
            .values_list('bot__player', 'match_count')
        match_counts = defaultdict(int, match_counts)

        for player in players:
            player.score_percent = Decimal(player.score) / score_max * 100
            player.top1_percent = float(player.top1) / top1_max * 100
            player.top10_percent = float(player.top10) / top10_max * 100
            player.match_count = match_counts[player.id]
            player.matches_percent = float(player.match_count) / matches_max * 100

        context.update({
            'player_list': players,
            'page': page,
        })

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

        page_num = self.request.GET.get('page', 1)
        page = Paginator(matches, 50).page(page_num)
        matches = page.object_list

        for match in matches:
            match.player, match.opponent = match.opponent_set.all()
        add_matches_stats(matches)

        context.update({
            'match_list': matches,
            'page': page,
        })

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
