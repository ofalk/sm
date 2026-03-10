from django import template

register = template.Library()

@register.filter
def get_history_diff(record):
    """
    Returns the changes between this record and its predecessor.
    """
    if not record.prev_record:
        return None
    
    diff = record.diff_against(record.prev_record)
    return diff.changes
