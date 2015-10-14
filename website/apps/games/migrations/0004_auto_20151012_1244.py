# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0003_auto_20151012_1234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='slug',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
