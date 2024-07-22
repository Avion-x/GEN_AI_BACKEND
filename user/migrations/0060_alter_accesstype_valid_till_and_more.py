# Generated by Django 5.0.1 on 2024-06-26 05:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0059_alter_accesstype_valid_till_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accesstype",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 6, 26, 5, 29, 24, 502637, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 6, 26, 5, 29, 24, 502637, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="customerconfig",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 6, 26, 5, 29, 24, 502637, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="requesttracking",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 6, 26, 5, 29, 24, 502637, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 6, 26, 5, 29, 24, 502637, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="useraccess",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 6, 26, 5, 29, 24, 502637, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
