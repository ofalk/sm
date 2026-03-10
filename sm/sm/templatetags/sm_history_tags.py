from django import template

register = template.Library()


@register.filter
def get_history_diff(record):
    """
    Returns the changes between this record and its predecessor.
    """
    if not record.prev_record:
        # If it's a change type but has no predecessor, it's likely the
        # first record created after history was enabled.
        if record.history_type == "~":
            return [{"field": "System", "old": "N/A", "new": "History enabled"}]
        return None

    diff = record.diff_against(record.prev_record)
    return diff.changes
