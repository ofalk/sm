from django.apps import AppConfig


class SmConfig(AppConfig):
    name = "sm"
    verbose_name = "Server Manager"

    def ready(self):
        from .patches import apply_patches

        apply_patches()

        # Import the module so its @receiver decorators are registered.
        from . import notifications  # noqa: F401
