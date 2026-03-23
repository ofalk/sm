# Generated manually 2026-03-23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("clusterpackagetype", "0004_historicalmodel"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="model",
            name="unique_sm_clusterpackagetype_name",
        ),
        migrations.AddField(
            model_name="historicalmodel",
            name="group",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="auth.group",
            ),
        ),
        migrations.AddField(
            model_name="model",
            name="group",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="clusterpackagetypes",
                to="auth.group",
            ),
        ),
        migrations.AddConstraint(
            model_name="model",
            constraint=models.UniqueConstraint(
                fields=("name", "group"), name="unique_sm_clusterpackagetype_name_group"
            ),
        ),
    ]
