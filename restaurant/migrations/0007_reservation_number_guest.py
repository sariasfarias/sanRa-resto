# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2020-06-04 22:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0006_guest_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='number_guest',
            field=models.IntegerField(default=0),
        ),
    ]
