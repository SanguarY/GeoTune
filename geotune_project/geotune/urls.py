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
    
    # Passwort-Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='geotune/registration/password_reset_form.html',
             email_template_name='geotune/registration/password_reset_email.html',
             subject_template_name='geotune/registration/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='geotune/registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='geotune/registration/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='geotune/registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Nutzerprofile
    path('profil/', views.nutzerprofil, name='nutzerprofil'),
    path('profil/<int:nutzer_id>/', views.nutzerprofil, name='nutzerprofil'),
    path('nutzer/suchen/', views.nutzer_suchen, name='nutzer_suchen'),
    path('nutzer/empfehlungen/', views.nutzer_empfehlungen, name='nutzer_empfehlungen'),
    path('password-change/', views.password_change, name='password_change'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('update-bio/', views.update_bio, name='update_bio'),
    path('update-profile-image/', views.update_profile_image, name='update_profile_image'),
    
    # Abonnement
    path('abonnement/', views.abonnement_verwalten, name='abonnement_verwalten'),
    path('abonnement/kuendigen/', views.kuendigen_abonnement, name='kuendigen_abonnement'),
    path('toggle-premium/', views.toggle_premium, name='toggle_premium'),  # Temporäre Route zum Testen
    
    # Punkte & Gamification
    path('punkte/', views.gamification, name='gamification'),
    
    # Events
    path('events/', views.events_liste, name='events'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/neu/', views.event_erstellen, name='event_erstellen'),
    path('events/<int:event_id>/bearbeiten/', views.event_bearbeiten, name='event_bearbeiten'),
    path('events/<int:event_id>/loeschen/', views.event_loeschen, name='event_loeschen'),
    path('events/<int:event_id>/teilnehmen/', views.event_teilnehmen, name='event_teilnehmen'),
    path('events/<int:event_id>/playlist-hinzufuegen/', views.event_playlist_hinzufuegen, name='event_playlist_hinzufuegen'),
    
    # Partner & Sponsoren
    path('partner/', views.partner_liste, name='partner'),
    
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
    
    # Geocaching
    path('geocaches/', views.geocache_liste, name='geocache_liste'),
    path('geocaches/<int:geocache_id>/', views.geocache_detail, name='geocache_detail'),
    path('geocaches/neu/', views.geocache_erstellen, name='geocache_erstellen'),
    path('geocaches/<int:geocache_id>/bearbeiten/', views.geocache_bearbeiten, name='geocache_bearbeiten'),
    path('geocaches/<int:geocache_id>/fund-registrieren/', views.geocache_fund_registrieren, name='geocache_fund_registrieren'),

    # Über GeoTune 
    path('ueber-uns/', views.ueber_uns, name='ueber_uns'),
    path('datenschutz/', views.datenschutz, name='datenschutz'),
    path('kontakt/', views.kontakt, name='kontakt'),
]