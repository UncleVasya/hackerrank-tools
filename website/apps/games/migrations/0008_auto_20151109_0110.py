# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0007_auto_20151107_0123'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bot',
            name='submitted_at',
        ),
        migrations.AddField(
            model_name='bot',
            name='rank',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='player',
            name='avatar',
            field=models.URLField(default='http://site.com'),
            preserve_default=False,
        ),
    ]
