# Generated by Django 5.0 on 2023-12-12 09:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="productcategory",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="productcategoryprompt",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="productcategorypromptcode",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="productprompt",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="productsubcategory",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="prompt",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="testtype",
            name="valid_till",
            field=models.DateField(blank=True, null=True),
        ),
    ]
