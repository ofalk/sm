from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("sm", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Invitation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("email", models.EmailField(max_length=254)),
                (
                    "token",
                    models.UUIDField(default=uuid.uuid4, unique=True),
                ),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="auth.group",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="invitations_sent",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Invitation",
                "verbose_name_plural": "Invitations",
            },
        ),
        migrations.AddConstraint(
            model_name="invitation",
            constraint=models.UniqueConstraint(
                fields=("email", "group"), name="sm_invitation_email_group_unique"
            ),
        ),
    ]
