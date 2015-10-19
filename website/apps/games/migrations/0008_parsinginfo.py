# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0007_match'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParsingInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('oldest_parsed_match', models.PositiveIntegerField(null=True)),
                ('newest_parsed_match', models.PositiveIntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
