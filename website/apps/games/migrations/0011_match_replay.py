# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-06-20 06:45
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0010_game_difficulty'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='replay',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]
