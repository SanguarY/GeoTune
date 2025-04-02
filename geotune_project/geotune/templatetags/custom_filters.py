from django import template
import re

register = template.Library()

@register.filter
def modulo(value, arg):
    """Gibt den Rest der Division von value durch arg zurück"""
    return int(value) % int(arg)

@register.filter
def intdiv(value, arg):
    """Gibt das Ergebnis der ganzzahligen Division von value durch arg zurück"""
    return int(value) // int(arg)

@register.filter
def add(value, arg):
    """Addiert zwei Zahlen"""
    return value + arg

@register.filter
def add_class(field, css_class):
    """Fügt einem Formularfeld eine CSS-Klasse hinzu"""
    return field.as_widget(attrs={"class": css_class})

@register.filter
def attr(field, attr_args):
    """Fügt einem Formularfeld ein beliebiges Attribut hinzu
    Verwendung: {{ field|attr:"name:value" }}
    """
    args = attr_args.split(':')
    if len(args) != 2:
        return field
    
    attr_name, attr_value = args
    
    if field.field.widget.attrs.get('class'):
        css_class = field.field.widget.attrs.get('class')
        return field.as_widget(attrs={attr_name: attr_value, 'class': css_class})
    else:
        return field.as_widget(attrs={attr_name: attr_value})