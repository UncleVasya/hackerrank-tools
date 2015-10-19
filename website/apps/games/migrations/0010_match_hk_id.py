# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0009_auto_20151019_1214'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='hk_id',
            field=models.PositiveIntegerField(default=None, unique=True),
            preserve_default=False,
        ),
    ]
