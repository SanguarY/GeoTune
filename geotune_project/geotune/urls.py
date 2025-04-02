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
    path('password-change/', views.password_change, name='password_change'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('update-bio/', views.update_bio, name='update_bio'),
    path('update-profile-image/', views.update_profile_image, name='update_profile_image'),
    
    # Verbindungen zwischen Nutzern
    path('verbindungen/', views.verbindungen, name='verbindungen'),
    path('verbindung/anfordern/<int:nutzer_id>/', views.verbindung_anfordern, name='verbindung_anfordern'),
    path('verbindung/status/<int:verbindung_id>/<str:neuer_status>/', views.verbindung_status_aendern, name='verbindung_status_aendern'),
    
    # Playlists
    path('playlist/neu/', views.playlist_erstellen, name='playlist_erstellen'),
    path('playlist/<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('playlist/<int:playlist_id>/standort-hinzufuegen/', views.playlist_standort_hinzufuegen, name='playlist_standort_hinzufuegen'),
    path('playlist/<int:playlist_id>/kommentar-hinzufuegen/', views.kommentar_hinzufuegen, name='kommentar_hinzufuegen'),
    path('playlist/<int:playlist_id>/toggle-favorite/', views.playlist_toggle_favorite, name='playlist_toggle_favorite'),
    path('playlist/<int:playlist_id>/bearbeiten/', views.playlist_bearbeiten, name='playlist_bearbeiten'),
    path('playlist/<int:playlist_id>/lied/<int:lied_id>/bearbeiten/', views.lied_bearbeiten, name='lied_bearbeiten'),
    path('playlist/<int:playlist_id>/lied/<int:lied_id>/loeschen/', views.lied_loeschen, name='lied_loeschen'),
    path('playlists/in-der-naehe/', views.playlists_in_der_naehe, name='playlists_in_der_naehe'),
    
    # Suchen (Playlist-Hunts)
    path('suche/neu/', views.suche_erstellen, name='suche_erstellen'),
    path('suche/<int:suche_id>/', views.suche_detail, name='suche_detail'),

    # Über GeoTune 
    path('ueber-uns/', views.ueber_uns, name='ueber_uns'),
    path('datenschutz/', views.datenschutz, name='datenschutz'),
    path('kontakt/', views.kontakt, name='kontakt'),
]