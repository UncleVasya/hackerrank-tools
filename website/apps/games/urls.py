from django.conf.urls import url
from apps.games.views import GameList

urlpatterns = [
    url(r'^$', GameList.as_view()),
    url(r'^games/$', GameList.as_view()),
]
