from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def subtract(value, arg):
    if value is None:
        value = Decimal('0')
    if arg is None:
        arg = Decimal('0')
    return value - arg

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg) if arg else 0
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def zip_lists(a, b):
    return zip(a, b)

@register.filter
def minus(value, arg):
    try:
        return float(value) - float(arg)
    except:
        return ''