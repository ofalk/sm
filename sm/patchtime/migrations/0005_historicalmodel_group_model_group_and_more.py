# Generated manually 2026-03-23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("patchtime", "0004_historicalmodel"),
    ]

    operations = [
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
                related_name="patchtimes",
                to="auth.group",
            ),
        ),
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
        migrations.AddConstraint(
            model_name="model",
            constraint=models.UniqueConstraint(
                fields=("name", "group"), name="unique_sm_patchtime_name_group"
            ),
        ),
    ]
