from django import template
from django.utils.safestring import mark_safe
from ..models import Playlist, PlaylistLied

register = template.Library()

@register.filter
def get_playlist_info(playlist_id):
    """Gibt Informationen über eine Playlist zurück."""
    if not playlist_id:
        return "Keine Informationen verfügbar"
    try:
        playlist = Playlist.objects.get(id=playlist_id)
        return f"Erstellt am {playlist.erstellungsdatum.strftime('%d.%m.%Y')}"
    except Playlist.DoesNotExist:
        return "Keine Informationen verfügbar"
    except ValueError:
        return "Keine Informationen verfügbar"

@register.filter
def get_playlist_song_count(playlist_id):
    """Gibt die Anzahl der Lieder in einer Playlist zurück."""
    if not playlist_id:
        return 0
    try:
        return PlaylistLied.objects.filter(playlist_id=playlist_id).count()
    except:
        return 0

@register.filter
def add_class(field, css_class):
    """Fügt eine CSS-Klasse zu einem Formularfeld hinzu."""
    return field.as_widget(attrs={'class': css_class}) 