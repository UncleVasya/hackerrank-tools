from django.contrib import admin
from django.db.models import Prefetch
from solo.admin import SingletonModelAdmin
from apps.games.models import Game, Bot, Player, ParsingInfo, Match


class BotInline(admin.TabularInline):
    model = Bot
    extra = 0

    fields = ['player', 'score', 'language', 'submitted_at']
    readonly_fields = ['player']

    def get_queryset(self, request):  # performance optimisation
        qs = super(BotInline, self).get_queryset(request)
        return qs.select_related('player')


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
    readonly_fields = ('bots',)

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
