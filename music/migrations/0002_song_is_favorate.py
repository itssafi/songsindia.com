# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-06-01 05:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='is_favorate',
            field=models.BooleanField(default=False),
        ),
    ]
