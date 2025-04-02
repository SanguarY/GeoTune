# views.py - Definition der Views für GeoTune

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, F, Sum
from django.contrib import messages
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, 
    NutzerVerbindung, PlaylistLied, Suche,
    NutzerPlaylistInteraktion, SuchePlaylist, NutzerSucheTeilnahme, 
    NutzerGenrePraeferenz, PlaylistStandort, Kommentar
)
from .forms import (
    PlaylistForm, LiedForm, NutzerProfilForm,
    StandortForm, SucheForm
)
from .forms import NutzerCreationForm
import json
from math import radians, cos, sin, asin, sqrt, atan2
from django.urls import reverse
import logging

def index(request):
    """Homepage-View"""
    if request.user.is_authenticated:
        # Für eingeloggte Nutzer personalisierte Inhalte anzeigen
        playlists = Playlist.objects.filter(
            ist_oeffentlich=True
        ).order_by('-erstellungsdatum')[:5]
        
        return render(request, 'geotune/index.html', {
            'playlists': playlists,
        })
    else:
        # Für nicht eingeloggte Nutzer generische Landing-Page
        return render(request, 'geotune/landing.html')

@login_required
def nutzerprofil(request, nutzer_id=None):
    """Profil-View für eigenes oder fremdes Profil"""
    if nutzer_id:
        # Fremdes Profil anzeigen
        profil_nutzer = get_object_or_404(Nutzer, id=nutzer_id)
        ist_eigenes_profil = (request.user.id == nutzer_id)
        
        # Verbindungsstatus prüfen
        verbindung = NutzerVerbindung.objects.filter(
            (Q(nutzer1=request.user) & Q(nutzer2=profil_nutzer)) |
            (Q(nutzer1=profil_nutzer) & Q(nutzer2=request.user))
        ).first()
        
        verbindungsstatus = None
        if verbindung:
            verbindungsstatus = verbindung.status
        
        # Öffentliche Playlists dieses Nutzers
        playlists = Playlist.objects.filter(
            erstellt_von=profil_nutzer, 
            ist_oeffentlich=True
        )
        
    else:
        # Eigenes Profil anzeigen
        profil_nutzer = request.user
        ist_eigenes_profil = True
        verbindungsstatus = None
        playlists = Playlist.objects.filter(erstellt_von=profil_nutzer)
    
    if request.method == 'POST' and ist_eigenes_profil:
        form = NutzerProfilForm(request.POST, request.FILES, instance=profil_nutzer)
        if form.is_valid():
            # Unterschiedliche Behandlung je nach geklicktem Button
            if 'update_profile' in request.POST:
                # Nur Profilinformationen speichern, ohne Genres
                profil = form.save(commit=False)
                profil.save()
                
                # Prüfen, ob AJAX-Anfrage
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Profil erfolgreich aktualisiert!',
                        'username': profil.username,
                        'first_name': profil.first_name,
                        'last_name': profil.last_name,
                    })
                else:
                    messages.success(request, 'Profil erfolgreich aktualisiert!')
            elif 'update_genres' in request.POST:
                # Nur Genres speichern
                ausgewaehlte_genres = form.cleaned_data['genrevorlieben']
                
                # Bestehende Genre-Präferenzen entfernen
                profil_nutzer.genre_praeferenzen.all().delete()
                
                # Neue Genre-Präferenzen erstellen
                for genre in ausgewaehlte_genres:
                    NutzerGenrePraeferenz.objects.create(
                        nutzer=profil_nutzer,
                        genre=genre,
                        praeferenzlevel=7  # Standard-Präferenzlevel
                    )
                
                # Prüfen, ob AJAX-Anfrage
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Bevorzugte Genres erfolgreich aktualisiert!'
                    })
                else:
                    messages.success(request, 'Bevorzugte Genres erfolgreich aktualisiert!')
            
            return redirect('nutzerprofil')
    else:
        form = NutzerProfilForm(instance=profil_nutzer) if ist_eigenes_profil else None
    
    return render(request, 'geotune/nutzerprofil.html', {
        'profil_nutzer': profil_nutzer,
        'ist_eigenes_profil': ist_eigenes_profil,
        'verbindungsstatus': verbindungsstatus,
        'playlists': playlists,
        'form': form,
    })

@login_required
def playlist_erstellen(request):
    """Neue Playlist erstellen"""
    if request.method == 'POST':
        form = PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.erstellt_von = request.user
            playlist.save()
            
            # Genres speichern (ManyToMany)
            form.save_m2m()
            
            # Genre-Verknüpfungen speichern
            if playlist.genres.count() > 0:
                playlist.genres.set(playlist.genres.all())
            
            messages.success(request, 'Playlist erfolgreich erstellt!', extra_tags='toast')
            return redirect('playlist_detail', playlist_id=playlist.id)
    else:
        form = PlaylistForm()
    
    return render(request, 'geotune/playlist_form.html', {'form': form})

@login_required
def playlist_detail(request, playlist_id):
    """Detailansicht einer Playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    # Überprüfen, ob der Nutzer diese Playlist sehen darf
    if not playlist.ist_oeffentlich and playlist.erstellt_von != request.user:
        messages.error(request, 'Du hast keine Berechtigung, diese Playlist anzusehen.')
        return redirect('index')
    
    # Playlist-Aufrufe erhöhen
    playlist.anzahl_aufrufe += 1
    playlist.save()
    
    # Interaktion speichern/aktualisieren
    interaktion, created = NutzerPlaylistInteraktion.objects.get_or_create( # type: ignore
        nutzer=request.user,
        playlist=playlist,
        defaults={'letzter_besuch': timezone.now(), 'besuchszaehler': 1}
    )
    if not created:
        interaktion.letzter_besuch = timezone.now()
        interaktion.besuchszaehler += 1
        interaktion.save()
    
    # Lieder der Playlist abrufen
    lieder = PlaylistLied.objects.filter(playlist=playlist).select_related('lied', 'hinzugefuegt_von')
    
    # Form für neue Lieder
    if request.method == 'POST':
        lied_form = LiedForm(request.POST)
        if lied_form.is_valid():
            lied = lied_form.save()
            # Lied zur Playlist hinzufügen
            playlist_lied = PlaylistLied.objects.create(
                playlist=playlist,
                lied=lied,
                hinzugefuegt_von=request.user
            )
            
            # AJAX-Anfrage behandeln
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Bereite Lied-Daten für die JSON-Antwort vor
                lied_data = {
                    'id': lied.id,
                    'titel': lied.titel,
                    'kuenstler': lied.kuenstler,
                    'album': lied.album,
                    'dauer': lied.dauer,
                    'externe_url': lied.externe_url,
                    'cover_bild': lied.cover_bild
                }
                
                # Sende JSON-Antwort
                return JsonResponse({
                    'success': True,
                    'message': 'Lied erfolgreich hinzugefügt!',
                    'lied': lied_data,
                })
            
            # Normale Anfrage
            messages.success(request, 'Lied erfolgreich hinzugefügt!', extra_tags='toast')
            return redirect('playlist_detail', playlist_id=playlist.id)
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Bei AJAX-Anfrage Fehler als JSON zurückgeben
            errors = {}
            for field, error_list in lied_form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'error': 'Bitte überprüfe die eingegebenen Daten.',
                'errors': errors
            }, status=400)
    else:
        lied_form = LiedForm()
    
    # Standorte abrufen
    standorte = PlaylistStandort.objects.filter(playlist=playlist).select_related('standort') # type: ignore
    
    # Kommentare abrufen
    kommentare = Kommentar.objects.filter(playlist=playlist).select_related('nutzer').order_by('-erstellungsdatum')
    
    return render(request, 'geotune/playlist_detail.html', {
        'playlist': playlist,
        'lieder': lieder,
        'lied_form': lied_form,
        'standorte': standorte,
        'ist_favorit': interaktion.ist_favorit,
        'kommentare': kommentare
    })

@login_required
def playlist_bearbeiten(request, playlist_id):
    """Playlist bearbeiten"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    # Überprüfen, ob der Nutzer berechtigt ist
    if playlist.erstellt_von != request.user:
        messages.error(request, 'Du hast keine Berechtigung, diese Playlist zu bearbeiten.')
        return redirect('playlist_detail', playlist_id=playlist.id)
    
    if request.method == 'POST':
        form = PlaylistForm(request.POST, instance=playlist)
        if form.is_valid():
            form.save()
            messages.success(request, 'Playlist erfolgreich aktualisiert!', extra_tags='toast')
            return redirect('playlist_detail', playlist_id=playlist.id)
    else:
        form = PlaylistForm(instance=playlist)
    
    return render(request, 'geotune/playlist_form.html', {
        'form': form,
        'playlist': playlist,
        'is_edit': True,
    })

@login_required
def lied_bearbeiten(request, playlist_id, lied_id):
    """Lied in einer Playlist bearbeiten"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    lied = get_object_or_404(Lied, id=lied_id)
    playlist_lied = get_object_or_404(PlaylistLied, playlist=playlist, lied=lied)
    
    # Überprüfen, ob der Nutzer berechtigt ist
    if playlist.erstellt_von != request.user:
        messages.error(request, 'Du hast keine Berechtigung, Lieder in dieser Playlist zu bearbeiten.')
        return redirect('playlist_detail', playlist_id=playlist.id)
    
    if request.method == 'POST':
        form = LiedForm(request.POST, instance=lied)
        if form.is_valid():
            form.save()
            
            # AJAX-Anfrage behandeln
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Bereite Lied-Daten für die JSON-Antwort vor
                lied_data = {
                    'id': lied.id,
                    'titel': lied.titel,
                    'kuenstler': lied.kuenstler,
                    'album': lied.album,
                    'dauer': lied.dauer,
                    'externe_url': lied.externe_url,
                    'cover_bild': lied.cover_bild
                }
                
                # Sende JSON-Antwort
                return JsonResponse({
                    'success': True,
                    'message': 'Lied erfolgreich aktualisiert!',
                    'lied': lied_data,
                })
            
            # Normale Anfrage
            messages.success(request, 'Lied erfolgreich aktualisiert!', extra_tags='toast')
            return redirect('playlist_detail', playlist_id=playlist.id)
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Bei AJAX-Anfrage Fehler als JSON zurückgeben
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'error': 'Bitte überprüfe die eingegebenen Daten.',
                'errors': errors
            }, status=400)
    else:
        # Für GET-Anfragen das Formular mit den aktuellen Daten befüllen
        form = LiedForm(instance=lied)
    
    # Bei normaler Anfrage JSON mit den Lied-Daten zurückgeben
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Format MM:SS für das Frontend berechnen
        minutes = lied.dauer // 60
        seconds = lied.dauer % 60
        dauer_format = f"{minutes}:{seconds:02d}"
        
        return JsonResponse({
            'success': True,
            'lied': {
                'id': lied.id,
                'titel': lied.titel,
                'kuenstler': lied.kuenstler,
                'album': lied.album,
                'dauer': lied.dauer,
                'dauer_format': dauer_format,
                'externe_url': lied.externe_url,
                'cover_bild': lied.cover_bild
            }
        })
    
    # Nicht-AJAX-Anfragen werden nicht unterstützt
    return redirect('playlist_detail', playlist_id=playlist.id)

@login_required
def lied_loeschen(request, playlist_id, lied_id):
    """Lied aus einer Playlist löschen"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    lied = get_object_or_404(Lied, id=lied_id)
    
    # Überprüfen, ob der Nutzer berechtigt ist
    if playlist.erstellt_von != request.user:
        messages.error(request, 'Du hast keine Berechtigung, Lieder aus dieser Playlist zu löschen.')
        return redirect('playlist_detail', playlist_id=playlist.id)
    
    # Sicherstellen, dass es einen PlaylistLied-Eintrag gibt
    playlist_lied = get_object_or_404(PlaylistLied, playlist=playlist, lied=lied)
    
    if request.method == 'POST':
        # PlaylistLied-Eintrag löschen
        playlist_lied.delete()
        
        # Prüfen, ob das Lied noch in anderen Playlists verwendet wird
        if not PlaylistLied.objects.filter(lied=lied).exists():
            # Wenn nicht, das Lied komplett löschen
            lied.delete()
        
        # AJAX-Anfrage behandeln
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Lied erfolgreich aus der Playlist entfernt!'
            })
        
        # Normale Anfrage
        messages.success(request, 'Lied erfolgreich aus der Playlist entfernt!')
    
    return redirect('playlist_detail', playlist_id=playlist.id)

@login_required
def playlist_standort_hinzufuegen(request, playlist_id):
    """Standort zu einer Playlist hinzufügen"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    # Überprüfen, ob der Nutzer berechtigt ist
    if playlist.erstellt_von != request.user:
        messages.error(request, 'Du hast keine Berechtigung, dieser Playlist einen Standort hinzuzufügen.')
        return redirect('playlist_detail', playlist_id=playlist.id)
    
    if request.method == 'POST':
        form = StandortForm(request.POST)
        if form.is_valid():
            standort = form.save()
            
            # Standort mit Playlist verknüpfen
            PlaylistStandort.objects.create( # type: ignore
                playlist=playlist,
                standort=standort,
                gueltig_von=timezone.now()
            )
            
            messages.success(request, 'Standort erfolgreich hinzugefügt!', extra_tags='toast')
            return redirect('playlist_detail', playlist_id=playlist.id)
    else:
        form = StandortForm()
    
    return render(request, 'geotune/standort_form.html', {
        'form': form,
        'playlist': playlist
    })

@login_required
def playlists_in_der_naehe(request):
    """Findet Playlists in der Nähe des aktuellen Standorts"""
    if request.method == 'POST':
        data = json.loads(request.body)
        lat = data.get('latitude')
        lng = data.get('longitude')
        max_distance = data.get('max_distance', 5)  # Standardmäßig 5 km
        
        # Alle Playlist-Standorte abrufen
        playlist_standorte = PlaylistStandort.objects.select_related('playlist', 'standort') # type: ignore
        
        def haversine(lon1, lat1, lon2, lat2):
            """
            Berechnung der Entfernung zwischen zwei Punkten auf der Erde
            über die Haversine-Formel
            """
            # Umwandlung in Radian
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            
            # Haversine-Formel
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Erdradius in km
            return c * r
        
        # Nahegelegene Playlists finden
        nahegelegene_playlists = []
        for ps in playlist_standorte:
            entfernung = haversine(lng, lat, ps.standort.laengengrad, ps.standort.breitengrad)
            if entfernung <= max_distance:
                nahegelegene_playlists.append({
                    'playlist_id': ps.playlist.id,
                    'playlist_name': ps.playlist.name,
                    'entfernung': round(entfernung, 2),
                    'standort': {
                        'lat': ps.standort.breitengrad,
                        'lng': ps.standort.laengengrad,
                        'adresse': ps.standort.adresse
                    }
                })
        
        return JsonResponse({
            'playlists': sorted(nahegelegene_playlists, key=lambda x: x['entfernung'])
        })
    
    return render(request, 'geotune/playlists_in_der_naehe.html')

@login_required
def suche_erstellen(request):
    """View zum Erstellen einer neuen Suche"""
    # Nur für eingeloggte Nutzer
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Holen der eigenen Playlists
    eigene_playlists = Playlist.objects.filter(erstellt_von=request.user).order_by('-erstellungsdatum')
    
    # Prüfen, ob Playlists mit Standorten existieren
    has_playlists_with_locations = any(playlist.standorte.count() > 0 for playlist in eigene_playlists)
    
    if request.method == 'POST':
        form = SucheForm(request.POST)
        if form.is_valid():
            suche = form.save(commit=False)
            suche.erstellt_von = request.user
            suche.save()
            
            # Ausgewählte Playlists mit Reihenfolge speichern
            playlists = request.POST.getlist('playlists')
            for i, playlist_id in enumerate(playlists, 1):
                try:
                    playlist = Playlist.objects.get(id=playlist_id, erstellt_von=request.user)
                    # Nur Playlists mit Standorten können hinzugefügt werden
                    if playlist.standorte.count() > 0:
                        SuchePlaylist.objects.create(
                            suche=suche,
                            playlist=playlist,
                            reihenfolge_nummer=i
                        )
                except Playlist.DoesNotExist:
                    pass
            
            messages.success(request, 'Playlist-Suche erfolgreich erstellt!', extra_tags='toast')
            return redirect('index')
    else:
        form = SucheForm()
    
    return render(request, 'geotune/suche_form.html', {
        'form': form,
        'eigene_playlists': eigene_playlists,
        'has_playlists_with_locations': has_playlists_with_locations,
    })

@login_required
def suche_detail(request, suche_id):
    """Detailansicht einer Playlist-Suche"""
    suche = get_object_or_404(Suche, id=suche_id)
    
    # Playlists dieser Suche abrufen
    suche_playlists = SuchePlaylist.objects.filter(
        suche=suche
    ).select_related('playlist').order_by('reihenfolge_nummer')
    
    # Teilnahme des aktuellen Nutzers
    teilnahme, created = NutzerSucheTeilnahme.objects.get_or_create(
        nutzer=request.user,
        suche=suche,
        defaults={'beitrittsdatum': timezone.now()}
    )
    
    # Teilnahmen aller Teilnehmer abrufen
    teilnehmer_infos = []
    for tn in suche.teilnehmer.all():
        try:
            tn_teilnahme = NutzerSucheTeilnahme.objects.filter(nutzer=tn, suche=suche).first()
            teilnehmer_infos.append({
                'nutzer': tn,
                'teilnahme': tn_teilnahme
            })
        except:
            pass
    
    return render(request, 'geotune/suche_detail.html', {
        'suche': suche,
        'suche_playlists': suche_playlists,
        'teilnahme': teilnahme,
        'teilnehmer_infos': teilnehmer_infos
    })

@login_required
def nutzer_suchen(request):
    """Suche nach anderen Nutzern"""
    suche = request.GET.get('q', '')
    
    if suche:
        nutzer = Nutzer.objects.filter(
            Q(username__icontains=suche) | 
            Q(first_name__icontains=suche) | 
            Q(last_name__icontains=suche)
        ).exclude(id=request.user.id)
    else:
        nutzer = []
    
    return render(request, 'geotune/nutzer_suchen.html', {
        'suche': suche,
        'nutzer': nutzer
    })

@login_required
def verbindung_anfordern(request, nutzer_id):
    """Verbindung zu einem anderen Nutzer anfordern"""
    ziel_nutzer = get_object_or_404(Nutzer, id=nutzer_id)
    
    # Prüfen, ob bereits eine Verbindung besteht
    bestehende_verbindung = NutzerVerbindung.objects.filter(
        (Q(nutzer1=request.user) & Q(nutzer2=ziel_nutzer)) |
        (Q(nutzer1=ziel_nutzer) & Q(nutzer2=request.user))
    ).first()
    
    if bestehende_verbindung:
        messages.info(request, f'Es besteht bereits eine Verbindung zu {ziel_nutzer.username} mit Status "{bestehende_verbindung.status}".')
    else:
        # Neue Verbindung erstellen
        NutzerVerbindung.objects.create(
            nutzer1=request.user,
            nutzer2=ziel_nutzer,
            status='angefragt'
        )
        messages.success(request, f'Verbindungsanfrage an {ziel_nutzer.username} gesendet!')
    
    # Überprüfen, woher die Anfrage kam (Referer prüfen)
    referer = request.META.get('HTTP_REFERER', '')
    if 'nutzer_empfehlungen' in referer:
        return redirect('nutzer_empfehlungen')
    else:
        return redirect('nutzerprofil', nutzer_id=nutzer_id)

@login_required
def verbindung_status_aendern(request, verbindung_id, neuer_status):
    """Status einer Verbindung ändern (akzeptieren/ablehnen/blockieren)"""
    verbindung = get_object_or_404(NutzerVerbindung, id=verbindung_id)
    
    # Prüfen, ob der Nutzer berechtigt ist
    if verbindung.nutzer2 != request.user:
        messages.error(request, 'Du hast keine Berechtigung, diese Verbindung zu ändern.')
        return redirect('verbindungen')
    
    if neuer_status in ['akzeptiert', 'blockiert']:
        verbindung.status = neuer_status
        verbindung.save()
        messages.success(request, f'Verbindung {neuer_status}.')
    else:
        # Verbindung ablehnen = löschen
        verbindung.delete()
        messages.success(request, 'Verbindung abgelehnt.')
    
    return redirect('verbindungen')

@login_required
def verbindungen(request):
    """Übersicht der Verbindungen eines Nutzers"""
    # Erhaltene Anfragen
    erhaltene_anfragen = NutzerVerbindung.objects.filter(
        nutzer2=request.user, 
        status='angefragt'
    ).select_related('nutzer1')
    
    # Gesendete Anfragen
    gesendete_anfragen = NutzerVerbindung.objects.filter(
        nutzer1=request.user, 
        status='angefragt'
    ).select_related('nutzer2')
    
    # Aktive Verbindungen
    aktive_verbindungen = NutzerVerbindung.objects.filter(
        (Q(nutzer1=request.user) | Q(nutzer2=request.user)),
        status='akzeptiert'
    ).select_related('nutzer1', 'nutzer2')
    
    # Für die Anzeige die jeweils andere Person bestimmen
    aktive_verbindungen_nutzer = []
    for v in aktive_verbindungen:
        andere_person = v.nutzer2 if v.nutzer1 == request.user else v.nutzer1
        aktive_verbindungen_nutzer.append({
            'verbindung': v,
            'nutzer': andere_person
        })
    
    return render(request, 'geotune/verbindungen.html', {
        'erhaltene_anfragen': erhaltene_anfragen,
        'gesendete_anfragen': gesendete_anfragen,
        'aktive_verbindungen': aktive_verbindungen_nutzer
    })

@login_required
def nutzer_empfehlungen(request):
    """Empfehlungen für Nutzer mit ähnlichem Musikgeschmack"""
    # Genres des aktuellen Nutzers
    nutzer_genres = NutzerGenrePraeferenz.objects.filter( # type: ignore
        nutzer=request.user
    ).values_list('genre_id', flat=True)
    
    # Nutzer mit ähnlichen Genres finden
    aehnliche_nutzer = Nutzer.objects.filter(
        genre_praeferenzen__genre_id__in=nutzer_genres
    ).exclude(
        id=request.user.id
    ).distinct()
    
    # Aktive Verbindungen abrufen
    verbundene_nutzer_ids = NutzerVerbindung.objects.filter(
        (Q(nutzer1=request.user) | Q(nutzer2=request.user)),
        status='akzeptiert'
    ).values_list(
        'nutzer1_id', 'nutzer2_id'
    ).distinct()
    
    # Flache Liste der verbundenen Nutzer IDs erstellen
    verbundene_ids = set()
    for n1, n2 in verbundene_nutzer_ids:
        verbundene_ids.add(n1)
        verbundene_ids.add(n2)
    
    # Nutzer, denen bereits eine Anfrage geschickt wurde, abrufen
    angefragt_ids = NutzerVerbindung.objects.filter(
        nutzer1=request.user,
        status='angefragt'
    ).values_list('nutzer2_id', flat=True)
    
    # Verbundene Nutzer und Nutzer mit ausstehenden Anfragen herausfiltern
    empfohlene_nutzer = aehnliche_nutzer.exclude(id__in=verbundene_ids).exclude(id__in=angefragt_ids)
    
    # Für jeden empfohlenen Nutzer die Playlist- und Verbindungszahlen berechnen
    empfohlene_nutzer_mit_daten = []
    for nutzer in empfohlene_nutzer:
        # Playlists zählen
        playlist_count = nutzer.erstellte_playlists.count()
        
        # Verbindungen zählen (akzeptierte)
        verbindungen_count = NutzerVerbindung.objects.filter(
            Q(nutzer1=nutzer, status='akzeptiert') | Q(nutzer2=nutzer, status='akzeptiert')
        ).count()
        
        empfohlene_nutzer_mit_daten.append({
            'nutzer': nutzer,
            'playlist_count': playlist_count,
            'verbindungen_count': verbindungen_count
        })
    
    return render(request, 'geotune/nutzer_empfehlungen.html', {
        'empfohlene_nutzer': empfohlene_nutzer_mit_daten
    })

def ueber_uns(request):
    """Über GeoTune Seite"""
    return render(request, 'geotune/ueber_uns.html')

def datenschutz(request):
    """Datenschutz Seite"""
    return render(request, 'geotune/datenschutz.html')

def kontakt(request):
    """Kontakt Seite"""
    return render(request, 'geotune/kontakt.html')

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

def register(request):
    """Registrierung für neue Nutzer"""
    if request.method == 'POST':
        form = NutzerCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Extrahiere gewählte Genres aus dem Formular
            selected_genres = form.cleaned_data.get('genrevorlieben')
            
            # Erstelle NutzerGenrePraeferenz-Objekte für jedes ausgewählte Genre
            if selected_genres:
                for genre in selected_genres:
                    NutzerGenrePraeferenz.objects.create(
                        nutzer=user,
                        genre=genre,
                        praeferenzlevel=7  # Standard-Präferenzlevel
                    )
            
            login(request, user)
            messages.success(request, 'Dein Account wurde erfolgreich erstellt!')
            return redirect('index')
    else:
        form = NutzerCreationForm()
    return render(request, 'geotune/registration/register.html', {'form': form, 'genres': Genre.objects.all()})

def custom_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('index')

@login_required
def kommentar_hinzufuegen(request, playlist_id):
    """Fügt einen Kommentar zu einer Playlist hinzu"""
    if request.method != 'POST':
        # Redirect to playlist detail page for non-POST requests
        return redirect('playlist_detail', playlist_id=playlist_id)
    
    # Get the playlist
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    # Extract the comment text from the request
    text = request.POST.get('text', '').strip()
    
    if not text:
        messages.error(request, 'Bitte gib einen Kommentartext ein.')
        return redirect('playlist_detail', playlist_id=playlist_id)
    
    # Create the comment
    kommentar = Kommentar.objects.create(
        playlist=playlist,
        nutzer=request.user,
        text=text
    )
    
    # Respond to AJAX requests with JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Generate avatar HTML
        if request.user.profilbild:
            avatar_html = f'<img src="{request.user.profilbild.url}" alt="{request.user.username}">'
        else:
            avatar_html = f'<div class="avatar-placeholder">{request.user.username[0].upper()}</div>'
        
        # Return a JSON response with the comment data
        return JsonResponse({
            'success': True,
            'kommentar': {
                'id': kommentar.id,
                'text': kommentar.text,
                'nutzer_name': kommentar.nutzer.username,
                'nutzer_id': kommentar.nutzer.id,
                'nutzer_url': reverse('nutzerprofil', args=[kommentar.nutzer.id]),
                'datum': kommentar.erstellungsdatum.strftime('%d.%m.%Y'),
                'zeit': kommentar.erstellungsdatum.strftime('%H:%M'),
                'avatar_html': avatar_html
            }
        })
    
    # Redirect to the playlist detail page for regular form submissions
    messages.success(request, 'Kommentar wurde erfolgreich hinzugefügt.')
    return redirect('playlist_detail', playlist_id=playlist_id)

@login_required
def playlist_toggle_favorite(request, playlist_id):
    """Toggle the favorite status of a playlist for the logged-in user."""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    user = request.user
    
    try:
        # Get or create interaction
        interaction, created = NutzerPlaylistInteraktion.objects.get_or_create(
            nutzer=user,
            playlist=playlist,
            defaults={'ist_favorit': True, 'letzter_besuch': timezone.now()}
        )
        
        if not created:
            # Toggle favorite status
            interaction.ist_favorit = not interaction.ist_favorit
            interaction.save()
        
        # Prepare message based on favorite status
        if interaction.ist_favorit:
            message_text = "Playlist wurde zu deinen Favoriten hinzugefügt."
        else:
            message_text = "Playlist wurde aus deinen Favoriten entfernt."
        
        # For AJAX requests, return a proper JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_favorite': interaction.ist_favorit,
                'message': message_text
            })
        
        # For normal form submissions, set a message and redirect
        messages.success(request, message_text)
        return redirect('playlist_detail', playlist_id=playlist_id)
        
    except Exception as e:
        # Log the error for server-side debugging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in playlist_toggle_favorite: {str(e)}", exc_info=True)
        
        # For AJAX requests, return an error response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': "Fehler beim Aktualisieren des Favoriten-Status"
            }, status=500)
        
        # For normal form submissions, set an error message and redirect
        messages.error(request, "Fehler beim Aktualisieren des Favoriten-Status")
        return redirect('playlist_detail', playlist_id=playlist_id)

@login_required
def password_change(request):
    """Ändert das Passwort des Nutzers"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Wichtig: Session-Auth-Hash aktualisieren, damit der Nutzer nicht ausgeloggt wird
            update_session_auth_hash(request, user)
            messages.success(request, 'Dein Passwort wurde erfolgreich geändert!')
            return redirect('nutzerprofil')
        else:
            for error in form.errors.values():
                messages.error(request, error)
            return redirect('nutzerprofil')
    else:
        return redirect('nutzerprofil')

@login_required
def delete_account(request):
    """Löscht den Account des Nutzers"""
    if request.method == 'POST':
        password = request.POST.get('password_confirm')
        user = request.user
        
        # Überprüfen, ob das eingegebene Passwort korrekt ist
        if user.check_password(password):
            # Account löschen
            try:
                # Alle verknüpften Daten müssen zuerst gelöscht werden
                # Dies hängt von den genauen Model-Beziehungen ab
                user.delete()
                messages.success(request, 'Dein Account wurde erfolgreich gelöscht.')
                logout(request)
                return redirect('index')
            except Exception as e:
                messages.error(request, f'Fehler beim Löschen des Accounts: {str(e)}')
                return redirect('nutzerprofil')
        else:
            messages.error(request, 'Das eingegebene Passwort ist nicht korrekt.')
            return redirect('nutzerprofil')
    else:
        return redirect('nutzerprofil')

@login_required
def update_bio(request):
    """Aktualisiert nur die Bio des Nutzers"""
    if request.method == 'POST':
        bio = request.POST.get('bio', '')
        user = request.user
        user.bio = bio
        user.save()
        
        # Prüfen, ob AJAX-Anfrage
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Bio erfolgreich aktualisiert!',
                'bio': bio
            })
        else:
            messages.success(request, 'Bio erfolgreich aktualisiert!')
            return redirect('nutzerprofil')
    
    return redirect('nutzerprofil')

@login_required
def update_profile_image(request):
    """Aktualisiert nur das Profilbild des Nutzers"""
    if request.method == 'POST' and request.FILES.get('profilbild'):
        user = request.user
        user.profilbild = request.FILES['profilbild']
        user.save()
        
        # Prüfen, ob AJAX-Anfrage
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Profilbild erfolgreich aktualisiert!',
                'image_url': user.profilbild.url if user.profilbild else None
            })
        else:
            messages.success(request, 'Profilbild erfolgreich aktualisiert!')
            return redirect('nutzerprofil')
    
    return redirect('nutzerprofil')