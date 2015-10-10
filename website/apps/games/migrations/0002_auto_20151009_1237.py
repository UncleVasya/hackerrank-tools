# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='game',
            options={'ordering': ['pk']},
        ),
        migrations.RemoveField(
            model_name='game',
            name='birth',
        ),
        migrations.AlterField(
            model_name='game',
            name='difficulty',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='hk_id',
            field=models.PositiveIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='name',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
