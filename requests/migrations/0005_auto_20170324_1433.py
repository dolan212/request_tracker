# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-24 14:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('requests', '0004_auto_20170320_1831'),
    ]

    operations = [
        migrations.AddField(
            model_name='update',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='queue',
            name='creators',
            field=models.ManyToManyField(blank=True, related_name='create_queues', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='queue',
            name='workers',
            field=models.ManyToManyField(blank=True, related_name='work_queues', to=settings.AUTH_USER_MODEL),
        ),
    ]