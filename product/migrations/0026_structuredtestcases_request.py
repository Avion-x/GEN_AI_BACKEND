# Generated by Django 5.0.1 on 2024-02-07 08:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0025_structuredtestcases"),
        ("user", "0015_alter_requesttracking_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="structuredtestcases",
            name="request",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="structured_test_cases",
                to="user.requesttracking",
            ),
        ),
    ]
