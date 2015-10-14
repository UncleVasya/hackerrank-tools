from django.conf.urls import url
from apps.games.views import GameList, GameDetail
from apps.games.views import PlayerList, PlayerDetail

urlpatterns = [
    url(r'^$', GameList.as_view()),

    url(r'^games/$', GameList.as_view()),
    url(r'^game/(?P<slug>[-\w]+)/$', GameDetail.as_view()),

    url(r'^players/$', PlayerList.as_view()),
    url(r'^player/(?P<slug>[-\w]+)/$', PlayerDetail.as_view()),

]
