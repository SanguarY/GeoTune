from django import template

register = template.Library()

@register.filter
def modulo(value, arg):
    """Gibt den Rest der Division von value durch arg zurück"""
    return int(value) % int(arg)

@register.filter
def intdiv(value, arg):
    """Gibt das Ergebnis der ganzzahligen Division von value durch arg zurück"""
    return int(value) // int(arg)