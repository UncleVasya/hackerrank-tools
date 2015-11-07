from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import Prefetch
from solo.admin import SingletonModelAdmin
from apps.games.models import Game, Bot, Player, ParsingInfo, Match, Opponent


class BotInline(admin.TabularInline):
    model = Bot
    extra = 0

    fields = ['player', 'score', 'language', 'submitted_at']
    readonly_fields = ['player']

    def get_queryset(self, request):  # performance optimisation
        qs = super(BotInline, self).get_queryset(request)
        return qs.select_related('player')


class BotMatchesInline(admin.TabularInline):
    model = Opponent
    verbose_name = 'Matches'
    extra = 0

    fields = ['hk_id', 'game', 'opponent', 'result', 'date', 'edit']
    readonly_fields = ['hk_id', 'game', 'opponent', 'result', 'date', 'edit']

    @staticmethod
    def hk_id(m2m):
        return m2m.match.hk_id

    @staticmethod
    def game(m2m):
        return m2m.match.game

    @staticmethod
    def opponent(m2m):
        bots = m2m.match.bots
        opponent = bots.exclude(pk=m2m.bot.pk).first()
        return opponent.player

    @staticmethod
    def result(m2m):
        result = m2m.match.result
        if result == 0:
            return 'Draw'
        if result == m2m.position:
            return 'Win'
        return 'Loss'

    @staticmethod
    def date(m2m):
        return m2m.match.date.date()

    def edit(self, m2m):
        return '<a href=%s>edit</a>' % \
               reverse('admin:games_match_change', args=[m2m.match.pk])
    edit.allow_tags = True

    def get_queryset(self, request):
        qs = super(BotMatchesInline, self).get_queryset(request)
        return qs.select_related('bot', 'bot__player', 'match', 'match__game')


class GameAdmin(admin.ModelAdmin):
    model = Game

    fieldsets = [
        (None, {'fields': [('name', 'difficulty', 'slug'), 'description']}),
    ]
    inlines = [BotInline]

    list_display = ('name', 'difficulty', 'description')


class BotAdmin(admin.ModelAdmin):
    model = Bot

    fieldsets = [
        (None, {'fields': [('score', 'language'), 'player', 'game']}),
    ]
    inlines = [BotMatchesInline]

    list_display = ('player', 'game', 'score')


class PlayerAdmin(admin.ModelAdmin):
    model = Player

    fieldsets = [
        (None, {'fields': [('name', 'country')]}),
    ]
    inlines = [BotInline]

    list_display = ('name', 'country')


class MatchAdmin(admin.ModelAdmin):
    model = Match

    fieldsets = [
        (None, {'fields': ['game', 'date', 'bots', ('message', 'result')]}),
    ]
    readonly_fields = ['bots']

    list_display = ('game', 'date')

    def get_queryset(self, request):  # performance optimisation
        qs = super(MatchAdmin, self).get_queryset(request)
        return qs.prefetch_related(Prefetch(
            'bots',
            queryset=Bot.objects.select_related('player', 'game')
        ))


admin.site.register(Game, GameAdmin)
admin.site.register(Bot, BotAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Match, MatchAdmin)

admin.site.register(ParsingInfo, SingletonModelAdmin)
