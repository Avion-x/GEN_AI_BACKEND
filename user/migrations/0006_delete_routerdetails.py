# Generated by Django 5.0.1 on 2024-01-04 11:33

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0005_alter_customerconfig_customer_alter_user_customer_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="RouterDetails",
        ),
    ]
