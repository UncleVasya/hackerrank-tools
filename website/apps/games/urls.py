from django.conf.urls import url
from apps.games.views import GameList, GameDetail
from apps.games.views import PlayerList, PlayerDetail

urlpatterns = [
    url(r'^$', GameList.as_view(),
        name='index'),

    url(r'^games/$', GameList.as_view(),
        name='game-list'),
    url(r'^games/(?P<slug>[-\w]+)/$', GameDetail.as_view(),
        name='game-detail'),

    url(r'^players/$', PlayerList.as_view(),
        name='player-list'),
    url(r'^players/(?P<slug>[-\w]+)/$', PlayerDetail.as_view(),
        name='player-detail'),
]
