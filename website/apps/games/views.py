from django.views.generic import ListView, DetailView
from apps.games.models import Game, Player


class GameList(ListView):
    model = Game


class GameDetail(DetailView):
    model = Game
    slug_field = 'slug__iexact'  # case-insensitive match


class PlayerList(ListView):
    model = Player


class PlayerDetail(DetailView):
    model = Player
    slug_field = 'name__iexact'

