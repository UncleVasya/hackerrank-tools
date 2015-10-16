# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0005_auto_20151012_1257'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bot',
            name='score',
            field=models.DecimalField(max_digits=15, decimal_places=12),
        ),
    ]
