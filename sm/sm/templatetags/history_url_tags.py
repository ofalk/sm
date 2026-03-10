from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def get_history_diff_url(record):
    """
    Returns the URL for the history diff view of a record.
    """
    app_label = record.instance._meta.app_label
    # All our models use 'Model' as the name, but we can get it dynamically
    model_name = record.instance._meta.model_name

    return reverse(
        "history_diff",
        kwargs={
            "app_label": app_label,
            "model_name": model_name,
            "history_id": record.history_id,
        },
    )
