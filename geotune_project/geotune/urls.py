# urls.py - URL-Patterns für GeoTune

from django.urls import path # type: ignore
from django.contrib.auth import views as auth_views # type: ignore
from . import views

urlpatterns = [
    # Hauptseiten
    path('', views.index, name='index'),

    # Kontoerstellung
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='geotune/registration/login.html'), name='login'), # type: ignore
    path('logout/', views.custom_logout, name='logout'),
    
    # Nutzerprofile
    path('profil/', views.nutzerprofil, name='nutzerprofil'),
    path('profil/<int:nutzer_id>/', views.nutzerprofil, name='nutzerprofil'),
    path('nutzer/suchen/', views.nutzer_suchen, name='nutzer_suchen'),
    path('nutzer/empfehlungen/', views.nutzer_empfehlungen, name='nutzer_empfehlungen'),
    
    # Verbindungen zwischen Nutzern
    path('verbindungen/', views.verbindungen, name='verbindungen'),
    path('verbindung/anfordern/<int:nutzer_id>/', views.verbindung_anfordern, name='verbindung_anfordern'),
    path('verbindung/status/<int:verbindung_id>/<str:neuer_status>/', views.verbindung_status_aendern, name='verbindung_status_aendern'),
    
    # Playlists
    path('playlist/neu/', views.playlist_erstellen, name='playlist_erstellen'),
    path('playlist/<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('playlist/<int:playlist_id>/standort-hinzufuegen/', views.playlist_standort_hinzufuegen, name='playlist_standort_hinzufuegen'),
    path('playlists/in-der-naehe/', views.playlists_in_der_naehe, name='playlists_in_der_naehe'),
    
    # Suchen (Playlist-Hunts)
    path('suche/neu/', views.suche_erstellen, name='suche_erstellen'),
    path('suche/<int:suche_id>/', views.suche_detail, name='suche_detail'),
]