import json

from django import template
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.utils.encoding import force_str

register = template.Library()


def _is_empty(value):
    """Return True for values that should not take up space on a detail page."""
    if value is None or value == [] or value == {} or value == ():
        return True
    if isinstance(value, str):
        return value.strip() in ("", "{}", "[]", "null")
    return False


def _choice_labels(field):
    try:
        return {str(key): force_str(label) for key, label in field.choices}
    except (AttributeError, TypeError):
        return {}


@register.filter
def has_value(field):
    """Whether a bound form field has a value worth showing."""
    try:
        return not _is_empty(field.value())
    except (AttributeError, TypeError):
        return False


@register.filter
def with_values(fields):
    """Return only layout items whose bound field has a visible value."""
    return [item for item in fields if item.get("field") and has_value(item["field"])]


def _render_list(value):
    """Render lists of simple values (e.g. tags) as a readable list."""
    if any(isinstance(item, (dict, list, tuple)) for item in value):
        return json.dumps(value, indent=2, default=force_str)
    return ", ".join(force_str(item) for item in value)


def _model_label(form_field, value):
    """Resolve a foreign key value even when the field queryset is scoped."""
    try:
        model = form_field.queryset.model
        obj = model._default_manager.filter(pk=value).first()
    except (AttributeError, TypeError, ValueError):
        return None
    return force_str(obj) if obj is not None else None


@register.filter
def display_value(field):
    """Render the value of a bound form field as read-only display text.

    Detail views reuse the model form, but its widgets are plain HTML inputs
    without Bootstrap classes. Rendering the raw value keeps the page calm and
    makes foreign keys and choice fields show their human-readable labels.
    """
    try:
        value = field.value()
    except (AttributeError, TypeError):
        return ""

    if _is_empty(value):
        return ""

    form_field = getattr(field, "field", None)

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(form_field, ModelMultipleChoiceField):
        if value and hasattr(value[0], "pk"):
            return _render_list(value)
        try:
            objects = form_field.queryset.model._default_manager.filter(pk__in=value)
            labels = {str(obj.pk): force_str(obj) for obj in objects}
        except (AttributeError, TypeError, ValueError):
            labels = {}
        return ", ".join(labels.get(str(item), force_str(item)) for item in value)

    if isinstance(form_field, ModelChoiceField):
        label = _model_label(form_field, value)
        if label is not None:
            return label
        return force_str(value)

    choices = _choice_labels(form_field) if form_field is not None else {}
    if choices:
        return choices.get(str(value), force_str(value))

    if isinstance(value, dict):
        return json.dumps(value, indent=2, default=force_str)

    if isinstance(value, (list, tuple)):
        return _render_list(value)

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                parsed = json.loads(stripped)
            except (TypeError, ValueError):
                pass
            else:
                if not _is_empty(parsed):
                    return json.dumps(parsed, indent=2, default=force_str)

    return force_str(value)
