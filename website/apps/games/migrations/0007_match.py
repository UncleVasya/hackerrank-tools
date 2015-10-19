# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0006_auto_20151015_0714'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.PositiveIntegerField()),
                ('message', models.TextField()),
                ('date', models.DateTimeField()),
                ('bots', models.ManyToManyField(to='games.Bot')),
                ('game', models.ForeignKey(to='games.Game')),
            ],
        ),
    ]
