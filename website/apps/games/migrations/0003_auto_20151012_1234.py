# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0002_auto_20151009_1237'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.FloatField()),
                ('language', models.CharField(max_length=200)),
                ('submitted_at', models.CharField(max_length=200)),
                ('hk_json', jsonfield.fields.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('country', models.CharField(max_length=200)),
                ('hk_id', models.PositiveIntegerField(unique=True)),
                ('hk_json', jsonfield.fields.JSONField()),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.AddField(
            model_name='game',
            name='slug',
            field=models.CharField(max_length=200, unique=True, null=True),
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
