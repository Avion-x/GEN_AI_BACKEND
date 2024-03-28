# Generated by Django 5.0.2 on 2024-03-26 09:06

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event_manager', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cronexecution',
            name='pickup_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='cronexecution',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 26, 9, 6, 8, 860225, tzinfo=datetime.timezone.utc)),
        ),
    ]
