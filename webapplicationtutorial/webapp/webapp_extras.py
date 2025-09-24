from django import template

register = template.Library()

@register.filter(name='replace')
def replace(value, arg):
    """
    Replaces a string with another.
    Usage: {{ "some_string"|replace:"_, " }}
    """
    return value.replace(arg.split(',')[0], arg.split(',')[1])