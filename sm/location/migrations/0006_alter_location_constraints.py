# Generated manually 2026-03-23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("location", "0005_historicalmodel_group_model_group"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="model",
            name="unique_sm_location_name_country",
        ),
        migrations.AddConstraint(
            model_name="model",
            constraint=models.UniqueConstraint(
                fields=("name", "country", "group"),
                name="unique_sm_location_name_country_group",
            ),
        ),
    ]
