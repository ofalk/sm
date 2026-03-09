import django.core.serializers.base
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


def patch_serializers():
    """
    Apply patches to django core serializers for better fixture loading.
    """

    # 1. Patch build_instance to handle RelatedObjectDoesNotExist during natural key resolution
    # This remains useful even without the library as it makes fixture loading more robust.
    def build_instance(Model, data, db):
        default_manager = Model._meta.default_manager
        pk = data.get(Model._meta.pk.attname)
        if (
            pk is None
            and hasattr(default_manager, "get_by_natural_key")
            and hasattr(Model, "natural_key")
        ):
            obj = Model(**data)
            obj._state.db = db
            try:
                # This call is sensitive to related objects not being loaded yet
                natural_key = obj.natural_key()
            except Exception:
                natural_key = None

            if natural_key:
                try:
                    data[Model._meta.pk.attname] = Model._meta.pk.to_python(
                        default_manager.db_manager(db)
                        .get_by_natural_key(*natural_key)
                        .pk
                    )
                except Exception:
                    pass
        return Model(**data)

    django.core.serializers.base.build_instance = build_instance


def apply_patches():
    patch_serializers()
