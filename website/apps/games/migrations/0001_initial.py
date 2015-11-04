# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.DecimalField(max_digits=15, decimal_places=12)),
                ('language', models.CharField(max_length=200)),
                ('submitted_at', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('description', models.TextField(null=True, blank=True)),
                ('difficulty', models.CharField(max_length=200, null=True)),
                ('slug', models.CharField(unique=True, max_length=200)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.PositiveIntegerField()),
                ('message', models.TextField()),
                ('date', models.DateTimeField()),
                ('hk_id', models.PositiveIntegerField(unique=True)),
                ('bots', models.ManyToManyField(to='games.Bot')),
                ('game', models.ForeignKey(to='games.Game')),
            ],
        ),
        migrations.CreateModel(
            name='ParsingInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('oldest_parsed_match', models.PositiveIntegerField(null=True, blank=True)),
                ('newest_parsed_match', models.PositiveIntegerField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('country', models.CharField(max_length=200, null=True)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.AddField(
            model_name='bot',
            name='game',
            field=models.ForeignKey(to='games.Game'),
        ),
        migrations.AddField(
            model_name='bot',
            name='player',
            field=models.ForeignKey(to='games.Player'),
        ),
    ]
