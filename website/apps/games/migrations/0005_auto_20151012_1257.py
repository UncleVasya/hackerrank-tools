# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0004_auto_20151012_1244'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bot',
            name='hk_json',
        ),
        migrations.RemoveField(
            model_name='game',
            name='hk_id',
        ),
        migrations.RemoveField(
            model_name='game',
            name='hk_json',
        ),
        migrations.RemoveField(
            model_name='player',
            name='hk_id',
        ),
        migrations.RemoveField(
            model_name='player',
            name='hk_json',
        ),
        migrations.AlterField(
            model_name='player',
            name='country',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
