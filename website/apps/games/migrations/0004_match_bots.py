# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0003_remove_match_bots'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='bots',
            field=models.ManyToManyField(to='games.Bot', through='games.MatchBotPosition'),
        ),
    ]
