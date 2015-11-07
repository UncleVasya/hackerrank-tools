# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0004_match_bots'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='match',
            options={'ordering': ['-date']},
        ),
        migrations.AlterModelOptions(
            name='matchbotposition',
            options={'ordering': ['position']},
        ),
    ]
