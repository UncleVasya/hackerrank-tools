# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(null=True, blank=True)),
                ('birth', models.DateField(null=True, blank=True)),
                ('difficulty', models.CharField(max_length=200)),
                ('hk_id', models.PositiveIntegerField()),
                ('hk_json', jsonfield.fields.JSONField()),
            ],
        ),
    ]
