# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0005_auto_20151104_1905'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='matchbotposition',
            options={'ordering': ('position',)},
        ),
    ]
