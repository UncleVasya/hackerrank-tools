from django.conf.urls import url
from apps.games.views import GameList, GameOverview, GameBots, GameBotsActive, \
    MatchList, MatchDetail, \
    PlayerBots, PlayerBotsActive, PlayerBotsChallenging, PlayerMatches
from apps.games.views import PlayerList, PlayerOverview

urlpatterns = [
    url(r'^$', GameList.as_view(),
        name='index'),

    # ============== GAMES PAGES ==================
    url(r'^games/$', GameList.as_view(),
        name='game-list'),
    url(r'^games/(?P<slug>[-\w]+)/$', GameOverview.as_view(),
        name='game-overview'),

    url(r'^games/(?P<slug>[-\w]+)/bots/$', GameBots.as_view(),
        name='game-bots'),
    url(r'^games/(?P<slug>[-\w]+)/bots/active/$', GameBotsActive.as_view(),
        name='game-bots-active'),

    # ============== PLAYERS PAGES ==================
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

    # ============== MATCHES PAGES ==================
    url(r'^matches/$', MatchList.as_view(),
        name='match-list'),
    url(r'^matches/(?P<slug>[-\w]+)/$', MatchDetail.as_view(),
        name='match-detail'),
]
