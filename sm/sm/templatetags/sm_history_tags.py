from django import template
from django.db import models

register = template.Library()


@register.filter
def get_history_diff(record):
    """
    Returns the changes between this record and its predecessor.
    If the field is a foreign key, resolve the ID to a string representation.
    """
    if not record.prev_record:
        # If it's a change type but has no predecessor, it's likely the
        # first record created after history was enabled.
        if record.history_type == "~":
            return [{"field": "System", "old": "N/A", "new": "History enabled"}]
        return None

    diff = record.diff_against(record.prev_record)
    model_class = record.instance.__class__
    enhanced_changes = []

    for change in diff.changes:
        field_name = change.field
        old_val = change.old
        new_val = change.new

        try:
            # Check if this field is a ForeignKey in the original model
            field = model_class._meta.get_field(field_name)
            if isinstance(field, models.ForeignKey):
                related_model = field.remote_field.model

                def resolve_fk(val):
                    if val is None or val == "":
                        return None
                    try:
                        # Try to get the object to use its string representation
                        obj = related_model.objects.get(pk=val)
                        return str(obj)
                    except related_model.DoesNotExist:
                        return f"ID {val} (deleted)"

                old_val = resolve_fk(old_val)
                new_val = resolve_fk(new_val)
        except Exception:
            # If any error occurs (e.g. field not found), keep the original values
            pass

        enhanced_changes.append({"field": field_name, "old": old_val, "new": new_val})

    return enhanced_changes
