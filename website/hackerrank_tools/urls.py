from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns(
    '',
    url(r'^', include('apps.games.urls', namespace='games')),
    url(r'^admin/', include(admin.site.urls)),
)
