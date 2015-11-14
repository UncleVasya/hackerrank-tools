# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0008_auto_20151109_0110'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bot',
            options={'ordering': ['rank']},
        ),
        migrations.RenameField(
            model_name='game',
            old_name='difficulty',
            new_name='difficulty_text',
        ),
    ]
