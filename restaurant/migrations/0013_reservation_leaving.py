# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2020-06-27 02:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0012_auto_20200626_2205'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='leaving',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]