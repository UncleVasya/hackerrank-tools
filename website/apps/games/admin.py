from django.contrib import admin
from apps.games.models import Game


class GameAdmin(admin.ModelAdmin):
    model = Game

    fieldsets = [
        (None, {'fields': [('name', 'difficulty'), 'description']}),
        (None, {'fields': [('hk_json', 'hk_id')]}),
    ]

    list_display = ('name', 'difficulty', 'description')

admin.site.register(Game, GameAdmin)
