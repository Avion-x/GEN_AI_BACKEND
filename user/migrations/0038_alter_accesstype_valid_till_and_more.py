# Generated by Django 5.0.2 on 2024-03-18 17:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0037_alter_accesstype_valid_till_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesstype',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 18, 17, 9, 23, 764933, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 18, 17, 9, 23, 764933, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='customerconfig',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 18, 17, 9, 23, 764933, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='requesttracking',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 18, 17, 9, 23, 764933, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='user',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 18, 17, 9, 23, 764933, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='useraccess',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 18, 17, 9, 23, 764933, tzinfo=datetime.timezone.utc)),
        ),
    ]
