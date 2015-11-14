# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0009_auto_20151112_0825'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='difficulty',
            field=models.FloatField(null=True),
        ),
    ]
