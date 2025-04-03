from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, 
    NutzerVerbindung, PlaylistLied, NutzerGenrePraeferenz,
    Suche, SuchePlaylist, NutzerSucheTeilnahme, Kommentar,
    Abonnement, Gamification, Partner, Event,
    Geocache, GeocacheFund
)

# Benutzerdefinierter UserAdmin
class NutzerAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'premium_status')
    fieldsets = UserAdmin.fieldsets + (
        ('GeoTune-Profil', {'fields': ('bio', 'profilbild', 'premium_status')}),
    )

class AbonnementAdmin(admin.ModelAdmin):
    list_display = ('nutzer', 'abo_typ', 'preis', 'startdatum', 'enddatum', 'aktiv')
    list_filter = ('abo_typ', 'aktiv')
    search_fields = ('nutzer__username',)

class GamificationAdmin(admin.ModelAdmin):
    list_display = ('nutzer', 'aktivitaet', 'punktewert', 'datum')
    list_filter = ('aktivitaet',)
    search_fields = ('nutzer__username',)

class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'typ', 'kontakt', 'kooperationsbeginn', 'kooperationsende')
    list_filter = ('typ',)
    search_fields = ('name', 'kontakt')

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'datum', 'ort', 'erstellt_von', 'partner')
    list_filter = ('datum',)
    search_fields = ('name', 'beschreibung')
    filter_horizontal = ('teilnehmer', 'playlists')

@admin.register(Geocache)
class GeocacheAdmin(admin.ModelAdmin):
    list_display = ('name', 'koordinaten', 'schwierigkeit', 'erstellt_von')
    list_filter = ('schwierigkeit', 'erstellt_von')
    search_fields = ('name', 'beschreibung')

@admin.register(GeocacheFund)
class GeocacheFundAdmin(admin.ModelAdmin):
    list_display = ('nutzer', 'geocache', 'funddatum')
    list_filter = ('funddatum', 'geocache')
    search_fields = ('nutzer__username', 'geocache__name')

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
admin.site.register(Abonnement, AbonnementAdmin)
admin.site.register(Gamification, GamificationAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(Event, EventAdmin)