from django import template

register = template.Library()


@register.filter(name='replace')
def replace(value, arg):
    """
    Replaces a string with another.
    Usage: {{ "some_string"|replace:"old,new" }}
    Returns the original value if the arg is malformed or an error occurs.
    """
    try:
        old, new = arg.split(',', 1)
    except Exception:
        return value

    try:
        s = str(value)
        return s.replace(old, new)
    except Exception:
        return value
