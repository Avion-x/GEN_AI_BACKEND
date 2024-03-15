# Generated by Django 4.2.9 on 2024-03-15 16:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0034_user_role_alter_accesstype_valid_till_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesstype',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 15, 16, 54, 59, 758809, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 15, 16, 54, 59, 758809, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='customerconfig',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 15, 16, 54, 59, 758809, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='requesttracking',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 15, 16, 54, 59, 758809, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='user',
            name='role_name',
            field=models.CharField(default='USER', max_length=255),
        ),
        migrations.AlterField(
            model_name='user',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 15, 16, 54, 59, 758809, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='useraccess',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 3, 15, 16, 54, 59, 758809, tzinfo=datetime.timezone.utc)),
        ),
    ]
