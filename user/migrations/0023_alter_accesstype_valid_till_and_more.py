# Generated by Django 4.2.9 on 2024-02-29 06:28

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('user', '0022_alter_accesstype_valid_till_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accesstype',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 2, 28, 6, 28, 1, 761848, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 2, 28, 6, 28, 1, 761848, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='customerconfig',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 2, 28, 6, 28, 1, 761848, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='requesttracking',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 2, 28, 6, 28, 1, 761848, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='user',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 2, 28, 6, 28, 1, 761848, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='useraccess',
            name='valid_till',
            field=models.DateField(default=datetime.datetime(2025, 2, 28, 6, 28, 1, 761848, tzinfo=datetime.timezone.utc)),
        ),
        migrations.CreateModel(
            name='Roles',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('group', models.ManyToManyField(related_name='roles', to='auth.group')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='user.roles'),
        ),
    ]
