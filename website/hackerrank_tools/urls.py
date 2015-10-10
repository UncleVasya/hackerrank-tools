from django.conf.urls import patterns, include, url

from django.contrib import admin

import hello.views

urlpatterns = patterns(
    '',
    url(r'^$', hello.views.index, name='index'),
    url(r'^db', hello.views.db, name='db'),
    url(r'^admin/', include(admin.site.urls)),
)
