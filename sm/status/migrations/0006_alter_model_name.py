# Generated manually 2026-03-23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("status", "0005_historicalmodel_group_model_group_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalmodel",
            name="name",
            field=models.CharField(max_length=45),
        ),
        migrations.AlterField(
            model_name="model",
            name="name",
            field=models.CharField(max_length=45),
        ),
    ]
