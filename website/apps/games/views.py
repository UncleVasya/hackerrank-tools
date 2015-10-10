from django.views.generic import ListView
from apps.games.models import Game


class GameList(ListView):
    model = Game
