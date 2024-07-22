# Generated by Django 5.0.1 on 2024-07-07 20:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("event_manager", "0017_alter_cronexecution_pickup_time_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cronexecution",
            name="pickup_time",
            field=models.DateTimeField(
                default=datetime.datetime(2024, 7, 8, 1, 55, 22, 918798)
            ),
        ),
        migrations.AlterField(
            model_name="cronexecution",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
