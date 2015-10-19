# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0008_parsinginfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parsinginfo',
            name='newest_parsed_match',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='parsinginfo',
            name='oldest_parsed_match',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
