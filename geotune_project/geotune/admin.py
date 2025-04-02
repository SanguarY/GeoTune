from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, 
    NutzerVerbindung, PlaylistLied, NutzerGenrePraeferenz,
    Suche, SuchePlaylist, NutzerSucheTeilnahme, Kommentar
)

# Benutzerdefinierter UserAdmin
class NutzerAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'premium_status')
    fieldsets = UserAdmin.fieldsets + (
        ('GeoTune-Profil', {'fields': ('bio', 'profilbild', 'premium_status')}),
    )

# Register models
admin.site.register(Nutzer, NutzerAdmin)
admin.site.register(Playlist)
admin.site.register(Lied)
admin.site.register(Genre)
admin.site.register(Standort)
admin.site.register(NutzerVerbindung)
admin.site.register(PlaylistLied)
admin.site.register(NutzerGenrePraeferenz)
admin.site.register(Suche)
admin.site.register(SuchePlaylist)
admin.site.register(NutzerSucheTeilnahme)
admin.site.register(Kommentar)