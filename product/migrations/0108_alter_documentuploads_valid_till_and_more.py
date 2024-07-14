# Generated by Django 5.0.1 on 2024-07-07 20:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0107_paramters_files_info_paramters_join_keys_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentuploads",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="foundationalmodel",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="knowledgebaseprompts",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="knowledgebaseresults",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="paramters",
            name="join_keys",
            field=models.JSONField(default={}),
        ),
        migrations.AlterField(
            model_name="paramters",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="productcategory",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="productcategoryprompt",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="productcategorypromptcode",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="productprompt",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="productsubcategory",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="prompt",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="runtimeparametervalues",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="structuredtestcases",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="testcases",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="testcategories",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="testscriptexecresults",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="testsubcategories",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="testtype",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="usercreatedtestcases",
            name="valid_till",
            field=models.DateField(
                default=datetime.datetime(
                    2025, 7, 7, 20, 25, 22, 862190, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
