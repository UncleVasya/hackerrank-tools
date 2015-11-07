# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0006_auto_20151105_0516'),
    ]

    operations = [
        migrations.CreateModel(
            name='Opponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.PositiveIntegerField()),
                ('bot', models.ForeignKey(to='games.Bot')),
            ],
            options={
                'ordering': ['position'],
            },
        ),
        migrations.RemoveField(
            model_name='matchbotposition',
            name='bot',
        ),
        migrations.RemoveField(
            model_name='matchbotposition',
            name='match',
        ),
        migrations.AlterField(
            model_name='match',
            name='bots',
            field=models.ManyToManyField(to='games.Bot', through='games.Opponent'),
        ),
        migrations.DeleteModel(
            name='MatchBotPosition',
        ),
        migrations.AddField(
            model_name='opponent',
            name='match',
            field=models.ForeignKey(to='games.Match'),
        ),
    ]
