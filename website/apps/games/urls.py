from django.conf.urls import url
from apps.games.views import GameList, GameDetail, MatchList, MatchDetail, PlayerBots, PlayerBotsActive, \
    PlayerBotsChallenging, PlayerMatches
from apps.games.views import PlayerList, PlayerOverview

urlpatterns = [
    url(r'^$', GameList.as_view(),
        name='index'),

    url(r'^games/$', GameList.as_view(),
        name='game-list'),
    url(r'^games/(?P<slug>[-\w]+)/$', GameDetail.as_view(),
        name='game-detail'),

    url(r'^players/$', PlayerList.as_view(),
        name='player-list'),
    url(r'^players/(?P<slug>[-\w]+)/$', PlayerOverview.as_view(),
        name='player-overview'),

    url(r'^players/(?P<slug>[-\w]+)/bots/$', PlayerBots.as_view(),
        name='player-bots'),
    url(r'^players/(?P<slug>[-\w]+)/bots/active/$', PlayerBotsActive.as_view(),
        name='player-bots-active'),
    url(r'^players/(?P<slug>[-\w]+)/bots/challenging/$', PlayerBotsChallenging.as_view(),
        name='player-bots-challenging'),


    url(r'^players/(?P<slug>[-\w]+)/matches/$', PlayerMatches.as_view(),
        name='player-matches'),

    url(r'^matches/$', MatchList.as_view(),
        name='match-list'),
    url(r'^matches/(?P<slug>[-\w]+)/$', MatchDetail.as_view(),
        name='match-detail'),
]
