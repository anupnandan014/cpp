from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Allows template syntax: {{ mydict|dict_get:key }}"""
    return d.get(key)
