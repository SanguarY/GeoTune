# views.py - Definition der Views für GeoTune

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.utils import timezone
from django.db.models import Q, Count, F, Sum
from django.contrib import messages
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, 
    NutzerVerbindung, PlaylistLied, Suche,
    NutzerPlaylistInteraktion, SuchePlaylist, NutzerSucheTeilnahme, 
    NutzerGenrePraeferenz, PlaylistStandort, Kommentar,
    Abonnement, Gamification, Partner, Event, Geocache, GeocacheFund
)
from .forms import (
    PlaylistForm, LiedForm, NutzerProfilForm,
    StandortForm, NutzerCreationForm,
    EventForm, EventPlaylistForm, AbonnementForm, GeocacheForm
)
from .forms import NutzerCreationForm
import json
from math import radians, cos, sin, asin, sqrt, atan2
from django.urls import reverse
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

# Hilfklassen für SQL-Abfragen, die direkt auf die Datenbank zugreifen
# Diese werden verwendet, wenn das ORM nicht ausreicht oder Kompatibilitätsprobleme bestehen
class DummyUser:
    """Hilfsklasse für Nutzer-Objekte, wenn direkte SQL-Abfragen verwendet werden"""
    def __init__(self, id, username):
        self.id = id
        self.username = username

class DummyLied:
    """Hilfsklasse für Lied-Objekte, wenn direkte SQL-Abfragen verwendet werden"""
    def __init__(self, id, titel, kuenstler, album, dauer, externe_url, cover_bild):
        self.id = id
        self.titel = titel
        self.kuenstler = kuenstler
        self.album = album
        self.dauer = dauer
        self.externe_url = externe_url
        self.cover_bild = cover_bild
        # Standard-Wert für Plattform setzen, um Fehler zu vermeiden
        self.plattform = ""

class DummyPlaylistLied:
    """Hilfsklasse für PlaylistLied-Objekte, wenn direkte SQL-Abfragen verwendet werden"""
    def __init__(self, id, lied, hinzugefuegt_von=None):
        self.id = id
        self.lied = lied
        self.hinzugefuegt_von = hinzugefuegt_von

# Hilfsfunktionen für gemeinsame Operationen
def is_ajax_request(request):
    """Prüft, ob es sich um eine AJAX-Anfrage handelt"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def ajax_success_response(message, **extra_data):
    """Erstellt eine erfolgreiche JSON-Antwort für AJAX-Anfragen"""
    response = {
        'success': True,
        'message': message
    }
    response.update(extra_data)
    return JsonResponse(response)

def ajax_error_response(message, errors=None, status=400):
    """Erstellt eine Fehler-JSON-Antwort für AJAX-Anfragen"""
    response = {
        'success': False,
        'message': message
    }
    if errors:
        if isinstance(errors, dict) and hasattr(errors, 'items'):
            # Wenn es Form-Errors sind, konvertiere sie in ein einfaches Dictionary
            form_errors = {}
            for field, error_list in errors.items():
                form_errors[field] = [str(error) for error in error_list]
            response['errors'] = form_errors
        else:
            response['errors'] = errors
    return JsonResponse(response, status=status)

def index(request):
    """Homepage-View mit personalisierten Inhalten für eingeloggte Nutzer"""
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
    """Profil-View für eigenes oder fremdes Profil mit Gamification-Elementen"""
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
    
    # Gamification-Daten für das Nutzerprofil abrufen
    total_punkte = Gamification.objects.filter(nutzer=profil_nutzer).aggregate(Sum('punktewert'))['punktewert__sum'] or 0
    
    # Level-System: 100 Punkte pro Level
    current_level = total_punkte // 100 + 1
    naechstes_level = current_level + 1
    punkte_bis_naechstes_level = 100 - (total_punkte % 100)
    level_progress = (total_punkte % 100)
    
    if request.method == 'POST' and ist_eigenes_profil:
        form = NutzerProfilForm(request.POST, request.FILES, instance=profil_nutzer)
        if form.is_valid():
            # Unterschiedliche Behandlung je nach geklicktem Button
            if 'update_profile' in request.POST:
                # Nur Profilinformationen speichern, ohne Genres
                profil = form.save(commit=False)
                profil.save()
                
                # Prüfen, ob AJAX-Anfrage
                if is_ajax_request(request):
                    return ajax_success_response(
                        'Profil erfolgreich aktualisiert!',
                        username=profil.username,
                        first_name=profil.first_name,
                        last_name=profil.last_name
                    )
                else:
                    messages.success(request, 'Profil erfolgreich aktualisiert!')
            elif 'update_genres' in request.POST:
                # Genres aus dem Formular extrahieren
                ausgewaehlte_genres = form.cleaned_data.get('genrevorlieben', [])
                
                # Bestehende Genre-Präferenzen entfernen
                NutzerGenrePraeferenz.objects.filter(nutzer=profil_nutzer).delete()
                
                # Neue Genre-Präferenzen erstellen
                for genre in ausgewaehlte_genres:
                    NutzerGenrePraeferenz.objects.create(
                        nutzer=profil_nutzer,
                        genre=genre,
                        praeferenzlevel=7  # Standard-Präferenzlevel
                    )
                
                # Prüfen, ob AJAX-Anfrage
                if is_ajax_request(request):
                    return ajax_success_response('Bevorzugte Genres erfolgreich aktualisiert!')
                else:
                    messages.success(request, 'Bevorzugte Genres erfolgreich aktualisiert!', extra_tags='toast')
            
            return redirect('nutzerprofil')
        else:
            # Form ist nicht valide
            if 'update_genres' in request.POST:
                messages.error(request, 'Es gab einen Fehler beim Aktualisieren der Genres.', extra_tags='toast')
                if is_ajax_request(request):
                    return ajax_error_response('Es gab einen Fehler beim Aktualisieren der Genres.', errors=form.errors)
    else:
        form = NutzerProfilForm(instance=profil_nutzer) if ist_eigenes_profil else None
    
    return render(request, 'geotune/nutzerprofil.html', {
        'profil_nutzer': profil_nutzer,
        'ist_eigenes_profil': ist_eigenes_profil,
        'verbindungsstatus': verbindungsstatus,
        'playlists': playlists,
        'form': form,
        'total_punkte': total_punkte,
        'current_level': current_level,
        'level_progress': level_progress,
        'punkte_bis_naechstes_level': punkte_bis_naechstes_level,
    })

@login_required
def playlist_erstellen(request):
    """Neue Playlist erstellen und mit Genres verknüpfen"""
    if request.method == 'POST':
        form = PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.erstellt_von = request.user
            playlist.save()
            
            # Genres speichern (ManyToMany)
            form.save_m2m()
            
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
    
    try:
        # Versuche, die Lieder mit Django ORM abzurufen
        lieder = PlaylistLied.objects.filter(
            playlist=playlist
        ).select_related('lied', 'hinzugefuegt_von')
    except Exception as e:
        # Fallback: Direkte SQL-Abfrage, wenn ORM fehlschlägt
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('''
            SELECT 
                pl.id, 
                l.id, 
                l.titel, 
                l.kuenstler, 
                l.album, 
                l.dauer, 
                l.externe_url, 
                l.cover_bild,
                u.id,
                u.username
            FROM 
                geotune_playlistlied pl
            JOIN 
                geotune_lied l ON pl.lied_id = l.id
            LEFT JOIN 
                geotune_nutzer u ON pl.hinzugefuegt_von_id = u.id
            WHERE 
                pl.playlist_id = %s
            ORDER BY 
                pl.datum_hinzugefuegt
        ''', [playlist.id])
        
        lieder_raw = cursor.fetchall()
        
        lieder = []
        for row in lieder_raw:
            pl_id, l_id, titel, kuenstler, album, dauer, externe_url, cover_bild, nutzer_id, username = row
            dummy_lied = DummyLied(l_id, titel, kuenstler, album, dauer, externe_url, cover_bild)
            dummy_user = DummyUser(nutzer_id, username)
            lieder.append(DummyPlaylistLied(pl_id, dummy_lied, dummy_user))
    
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
            if is_ajax_request(request):
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
                
                return ajax_success_response('Lied erfolgreich hinzugefügt!', lied=lied_data)
            
            # Normale Anfrage
            messages.success(request, 'Lied erfolgreich hinzugefügt!', extra_tags='toast')
            return redirect('playlist_detail', playlist_id=playlist.id)
        elif is_ajax_request(request):
            # Bei AJAX-Anfrage Fehler als JSON zurückgeben
            return ajax_error_response('Bitte überprüfe die eingegebenen Daten.', errors=lied_form.errors)
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
    
    # Lied mit manueller SQL-Abfrage abrufen, um die fehlende Plattform-Spalte zu umgehen
    try:
        lied = get_object_or_404(Lied, id=lied_id)
        playlist_lied = get_object_or_404(PlaylistLied, playlist=playlist, lied=lied)
    except Exception as e:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('''
            SELECT 
                l.id, 
                l.titel, 
                l.kuenstler, 
                l.album, 
                l.dauer, 
                l.externe_url, 
                l.cover_bild,
                pl.id as playlist_lied_id
            FROM 
                geotune_lied l
            JOIN 
                geotune_playlistlied pl ON pl.lied_id = l.id  
            WHERE 
                l.id = %s AND pl.playlist_id = %s
        ''', [lied_id, playlist_id])
        
        lied_data = cursor.fetchone()
        if not lied_data:
            raise Http404("Lied not found")
            
        l_id, titel, kuenstler, album, dauer, externe_url, cover_bild, pl_id = lied_data
        lied = DummyLied(l_id, titel, kuenstler, album, dauer, externe_url, cover_bild)
        playlist_lied = DummyPlaylistLied(pl_id, lied)
    
    # Überprüfen, ob der Nutzer berechtigt ist
    if playlist.erstellt_von != request.user:
        messages.error(request, 'Du hast keine Berechtigung, Lieder in dieser Playlist zu bearbeiten.')
        return redirect('playlist_detail', playlist_id=playlist.id)
    
    if request.method == 'POST':
        form = LiedForm(request.POST, instance=lied)
        if form.is_valid():
            try:
                # Speichere das Lied und fange potenzielle DB-Fehler ab
                lied = form.save()
                
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
            except Exception as e:
                # Fehlerbehandlung für DB-Probleme
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': f'Fehler beim Speichern: {str(e)}',
                    }, status=500)
                messages.error(request, f'Fehler beim Aktualisieren: {str(e)}')
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
    """Findet Playlists in der Nähe des aktuellen Standorts (Geocaching-Prinzip)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')
            max_distance = data.get('max_distance', 20)  # Standardmäßig 20 km für Anzeige
            
            # Basic validation
            if lat is None or lng is None:
                return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)
                
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
                    # Überprüfen, ob die Playlist abspielbar ist (Entfernung < 0.5 km)
                    is_playable = entfernung <= 0.5  # 500 Meter
                    
                    # Skip geocache functionality for now since the table doesn't exist
                    nahegelegene_playlists.append({
                        'playlist_id': ps.playlist.id,
                        'playlist_name': ps.playlist.name,
                        'entfernung': round(entfernung, 2),
                        'is_playable': is_playable,
                        'standort': {
                            'lat': ps.standort.breitengrad,
                            'lng': ps.standort.laengengrad,
                            'adresse': ps.standort.adresse
                        },
                        'geocaches': []  # Empty list instead of querying
                    })
            
            return JsonResponse({
                'playlists': sorted(nahegelegene_playlists, key=lambda x: x['entfernung'])
            })
        except json.JSONDecodeError as e:
            # Specific handling for JSON parsing errors
            logger = logging.getLogger(__name__)
            logger.error(f"JSON decode error in playlists_in_der_naehe: {str(e)}")
            # Log the problematic request body for debugging
            logger.error(f"Request body: {request.body}")
            return JsonResponse({'error': f'Invalid JSON data: {str(e)}'}, status=400)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in playlists_in_der_naehe: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
    
    return render(request, 'geotune/playlists_in_der_naehe.html')

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
        messages.info(request, f'Es besteht bereits eine Verbindung zu {ziel_nutzer.username} mit Status "{bestehende_verbindung.status}".', extra_tags='toast')
    else:
        # Neue Verbindung erstellen
        NutzerVerbindung.objects.create(
            nutzer1=request.user,
            nutzer2=ziel_nutzer,
            status='angefragt'
        )
        messages.success(request, f'Verbindungsanfrage an {ziel_nutzer.username} gesendet!', extra_tags='toast')
    
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
        if neuer_status == 'akzeptiert':
            messages.success(request, f'Verbindung mit {verbindung.nutzer1.username} akzeptiert.', extra_tags='toast')
        else:
            messages.success(request, f'Verbindung mit {verbindung.nutzer1.username} blockiert.', extra_tags='toast')
    else:
        # Verbindung ablehnen = löschen
        nutzer_name = verbindung.nutzer1.username
        verbindung.delete()
        messages.success(request, f'Verbindung mit {nutzer_name} abgelehnt.', extra_tags='toast')
    
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
            messages.success(request, 'Dein Account wurde erfolgreich erstellt!', extra_tags='toast')
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
        
        # Get preserved form data
        preserved_first_name = request.POST.get('preserved_first_name', '')
        preserved_last_name = request.POST.get('preserved_last_name', '')
        
        # Check if form is valid
        if form.is_valid():
            user = form.save()
            # Wichtig: Session-Auth-Hash aktualisieren, damit der Nutzer nicht ausgeloggt wird
            update_session_auth_hash(request, user)
            messages.success(request, 'Dein Passwort wurde erfolgreich geändert!')
            return redirect('nutzerprofil')
        else:
            # If password validation failed, directly update user fields to preserved values
            # This ensures the user object will have these values when rendering the form again
            if preserved_first_name:
                request.user.first_name = preserved_first_name
            if preserved_last_name:
                request.user.last_name = preserved_last_name

            # Don't save the user object - just keep the values for this request
            # The form will be re-rendered with these values
                
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
        if is_ajax_request(request):
            return ajax_success_response('Bio erfolgreich aktualisiert!', bio=bio)
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
        if is_ajax_request(request):
            return ajax_success_response(
                'Profilbild erfolgreich aktualisiert!', 
                image_url=user.profilbild.url if user.profilbild else None
            )
        else:
            messages.success(request, 'Profilbild erfolgreich aktualisiert!')
            return redirect('nutzerprofil')
    
    return redirect('nutzerprofil')

# ======================================
# ABONNEMENT-VERWALTUNG
# ======================================

@login_required
def toggle_premium(request):
    """Temporäre Funktion zum Umschalten des Premium-Status (nur zum Testen)"""
    if request.method == 'POST':
        user = request.user
        # Premium-Status umschalten
        user.premium_status = not user.premium_status
        user.save()
        
        # Zurück zum Profil
        return redirect('nutzerprofil', nutzer_id=user.id)
    return redirect('nutzerprofil', nutzer_id=request.user.id)

@login_required
def abonnement_verwalten(request):
    """Abonnement-Verwaltungsseite mit Abo-Optionen"""
    
    # Aktuelles Abonnement des Nutzers
    try:
        user_abo = Abonnement.objects.get(nutzer=request.user)
    except Abonnement.DoesNotExist:
        user_abo = None
    
    if request.method == 'POST':
        abo_typ = request.POST.get('abo_typ')
        
        # Abo-Preise (in €)
        abo_preise = {
            'basic': Decimal('0.00'),
            'premium': Decimal('3.99'),
            'pro': Decimal('8.99')
        }
        
        if abo_typ in abo_preise:
            # Premium-Status basierend auf abo_typ setzen
            if abo_typ in ['premium', 'pro']:
                request.user.premium_status = True
            else:
                request.user.premium_status = False
            request.user.save()
            
            # Wenn der Nutzer bereits ein Abo hat, aktualisieren
            if user_abo:
                user_abo.abo_typ = abo_typ
                user_abo.preis = abo_preise[abo_typ]
                user_abo.startdatum = timezone.now().date()
                user_abo.enddatum = None  # Zurücksetzen bei Abo-Änderung
                user_abo.aktiv = True
                user_abo.save()
                
                # Gamification: Punkte für Abo-Upgrade (wenn höherwertiger)
                if abo_typ in ['premium', 'pro'] and user_abo.abo_typ == 'basic':
                    Gamification.objects.create(
                        nutzer=request.user,
                        aktivitaet='abo_upgrade',
                        punktewert=20,
                        datum=timezone.now()
                    )
            else:
                # Neues Abonnement erstellen
                user_abo = Abonnement.objects.create(
                    nutzer=request.user,
                    abo_typ=abo_typ,
                    preis=abo_preise[abo_typ],
                    startdatum=timezone.now().date(),
                    aktiv=True
                )
            
            # AJAX-Anfrage behandeln
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Dein Abonnement wurde erfolgreich auf {user_abo.get_abo_typ_display()} aktualisiert.',
                    'plan': abo_typ
                })
            
            # Keine Django-Message mehr, nur URL-Parameter für Toast
            base_url = reverse('abonnement_verwalten')
            return HttpResponseRedirect(f'{base_url}?message=upgraded&plan={abo_typ}')
    
    return render(request, 'geotune/abonnement.html', {
        'user_abo': user_abo
    })

@login_required
def kuendigen_abonnement(request):
    """Abonnement kündigen"""
    if request.method == 'POST':
        try:
            abo = Abonnement.objects.get(nutzer=request.user)
            
            # Auf Basic zurücksetzen
            abo.abo_typ = 'basic'
            abo.preis = Decimal('0.00')
            abo.enddatum = timezone.now().date()
            
            # Premium-Status explizit zurücksetzen
            request.user.premium_status = False
            request.user.save()
            
            abo.save()
            
            # AJAX-Anfrage behandeln
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Dein Premium-Abonnement wurde gekündigt. Du nutzt jetzt den Basic-Plan.',
                })
            
            # Keine Django-Message mehr, nur URL-Parameter für Toast
            base_url = reverse('abonnement_verwalten')
            return HttpResponseRedirect(f'{base_url}?message=cancelled')
        except Abonnement.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Du hast kein aktives Abonnement, das gekündigt werden kann.',
                }, status=400)
            
            messages.error(request, 'Du hast kein aktives Abonnement, das gekündigt werden kann.')
    
    return redirect('abonnement_verwalten')

# ======================================
# GAMIFICATION & PUNKTE
# ======================================

@login_required
def gamification(request):
    """Anzeige der Gamification-Punkte und Aktivitäten"""
    
    # Alle Punkte des Nutzers abrufen und paginieren
    punkte = Gamification.objects.filter(nutzer=request.user).order_by('-datum')
    
    paginator = Paginator(punkte, 10)  # 10 Einträge pro Seite
    page = request.GET.get('page')
    
    try:
        punkte_liste = paginator.page(page)
    except PageNotAnInteger:
        # Wenn page keine Ganzzahl ist, zeige die erste Seite
        punkte_liste = paginator.page(1)
    except EmptyPage:
        # Wenn page außerhalb des Bereichs liegt, zeige die letzte Seite
        punkte_liste = paginator.page(paginator.num_pages)
    
    # Gesamtpunkte berechnen
    total_punkte = Gamification.objects.filter(nutzer=request.user).aggregate(Sum('punktewert'))['punktewert__sum'] or 0
    
    # Level-System: 100 Punkte pro Level
    current_level = total_punkte // 100 + 1
    naechstes_level = current_level + 1
    punkte_bis_naechstes_level = 100 - (total_punkte % 100)
    level_progress = (total_punkte % 100)
    
    return render(request, 'geotune/gamification.html', {
        'punkte_liste': punkte_liste,
        'total_punkte': total_punkte,
        'current_level': current_level,
        'naechstes_level': naechstes_level,
        'punkte_bis_naechstes_level': punkte_bis_naechstes_level,
        'level_progress': level_progress
    })

# ======================================
# EVENT-MANAGEMENT
# ======================================

@login_required
def events_liste(request):
    """Liste aller Events mit Filtermöglichkeiten"""
    
    # Grundlegende Abfrage aller Events
    events_queryset = Event.objects.all().order_by('datum')
    
    # Filter anwenden
    q = request.GET.get('q')
    datum_von = request.GET.get('datum_von')
    datum_bis = request.GET.get('datum_bis')
    
    if q:
        events_queryset = events_queryset.filter(
            Q(name__icontains=q) |
            Q(beschreibung__icontains=q) |
            Q(erstellt_von__username__icontains=q)
        )
    
    if datum_von:
        events_queryset = events_queryset.filter(datum__gte=datum_von)
    
    if datum_bis:
        events_queryset = events_queryset.filter(datum__lte=datum_bis)
    
    # Paginierung
    paginator = Paginator(events_queryset, 12)  # 12 Events pro Seite
    page = request.GET.get('page')
    
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)
    
    return render(request, 'geotune/events.html', {
        'events': events
    })

@login_required
def event_detail(request, event_id):
    """Detailansicht eines Events"""
    event = get_object_or_404(Event, id=event_id)
    
    return render(request, 'geotune/event_detail.html', {
        'event': event,
        'now': timezone.now()
    })

@login_required
def event_erstellen(request):
    """Neues Event erstellen"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.erstellt_von = request.user
            event.save()
            
            messages.success(request, 'Event erfolgreich erstellt!', extra_tags='toast')
            
            # Gamification: Punkte für Event-Erstellung
            Gamification.objects.create(
                nutzer=request.user,
                aktivitaet='event_erstellen',
                punktewert=25,
                datum=timezone.now()
            )
            
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm()
    
    return render(request, 'geotune/event_form.html', {
        'form': form,
        'is_new': True
    })

@login_required
def event_bearbeiten(request, event_id):
    """Event bearbeiten"""
    event = get_object_or_404(Event, id=event_id)
    
    # Nur der Ersteller darf bearbeiten
    if event.erstellt_von != request.user:
        messages.error(request, 'Du bist nicht berechtigt, dieses Event zu bearbeiten.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event erfolgreich aktualisiert!', extra_tags='toast')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'geotune/event_form.html', {
        'form': form,
        'event': event,
        'is_new': False
    })

@login_required
def event_loeschen(request, event_id):
    """Event löschen"""
    event = get_object_or_404(Event, id=event_id)
    
    # Nur der Ersteller darf löschen
    if event.erstellt_von != request.user:
        messages.error(request, 'Du bist nicht berechtigt, dieses Event zu löschen.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event erfolgreich gelöscht!', extra_tags='toast')
        return redirect('events')
    
    return redirect('event_detail', event_id=event.id)

@login_required
def event_teilnehmen(request, event_id):
    """Teilnahme an einem Event"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        # Prüfen, ob der Nutzer bereits Teilnehmer ist
        if request.user in event.teilnehmer.all():
            # Teilnahme entfernen
            event.teilnehmer.remove(request.user)
            messages.success(request, 'Du nimmst nicht mehr am Event teil.', extra_tags='toast')
        else:
            # Überprüfen, ob maximale Teilnehmerzahl erreicht ist
            if event.max_teilnehmer and event.teilnehmer.count() >= event.max_teilnehmer:
                messages.error(request, 'Das Event ist bereits ausgebucht!', extra_tags='toast')
            else:
                # Teilnahme hinzufügen
                event.teilnehmer.add(request.user)
                messages.success(request, 'Du nimmst jetzt am Event teil!', extra_tags='toast')
                
                # Überprüfen, ob der Nutzer bereits heute Punkte für Event-Teilnahme bekommen hat
                # Dies verhindert, dass ein Nutzer mehrere Event-Teilnahmen am gleichen Tag sammeln kann
                already_has_points_today = Gamification.objects.filter(
                    nutzer=request.user,
                    aktivitaet='event_teilnahme',
                    datum__date=timezone.now().date()
                ).exists()
                
                # Punkte nur vergeben, wenn der Nutzer noch keine Punkte für Event-Teilnahme heute bekommen hat
                if not already_has_points_today:
                    # Gamification: Punkte für Event-Teilnahme
                    try:
                        # Versuchen, mit referenz_id zu erstellen (falls das Feld existiert)
                        Gamification.objects.create(
                            nutzer=request.user,
                            aktivitaet='event_teilnahme',
                            punktewert=30,
                            datum=timezone.now(),
                            referenz_id=event.id
                        )
                    except:
                        # Fallback ohne referenz_id, wenn das Feld noch nicht existiert
                        Gamification.objects.create(
                            nutzer=request.user,
                            aktivitaet='event_teilnahme',
                            punktewert=30,
                            datum=timezone.now()
                        )
    
    # Bei AJAX-Anfrage JSON zurückgeben
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'teilnehmer_count': event.teilnehmer.count(),
            'user_nimmt_teil': request.user in event.teilnehmer.all()
        })
    
    # Andernfalls zur Event-Detailseite weiterleiten
    return redirect('event_detail', event_id=event.id)

@login_required
def event_playlist_hinzufuegen(request, event_id):
    """Playlists zu einem Event hinzufügen"""
    event = get_object_or_404(Event, id=event_id)
    
    # Nur der Ersteller darf Playlists hinzufügen
    if event.erstellt_von != request.user:
        messages.error(request, 'Du bist nicht berechtigt, Playlists zu diesem Event hinzuzufügen.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventPlaylistForm(request.POST, user=request.user)
        if form.is_valid():
            selected_playlists = form.cleaned_data['playlists']
            
            # Playlists zum Event hinzufügen
            for playlist in selected_playlists:
                event.playlists.add(playlist)
            
            messages.success(request, 'Playlists erfolgreich zum Event hinzugefügt!', extra_tags='toast')
            return redirect('event_detail', event_id=event.id)
    else:
        # Vorauswahl: Bereits dem Event zugeordnete Playlists
        initial_playlists = event.playlists.filter(erstellt_von=request.user)
        form = EventPlaylistForm(user=request.user, initial={'playlists': initial_playlists})
    
    return render(request, 'geotune/event_playlist_form.html', {
        'form': form,
        'event': event
    })

# ======================================
# PARTNER & SPONSOREN
# ======================================

def partner_liste(request):
    """Liste aller Partner und Sponsoren"""
    
    # Partner nach Typen gruppieren
    sponsoren = Partner.objects.filter(typ='sponsor')
    werbekunden = Partner.objects.filter(typ='werbekunde')
    kooperationspartner = Partner.objects.filter(typ='kooperation')
    
    return render(request, 'geotune/partner.html', {
        'sponsoren': sponsoren,
        'werbekunden': werbekunden,
        'kooperationspartner': kooperationspartner
    })

# Neue Geocache-Views
@login_required
def geocache_liste(request):
    """Liste aller Geocaches"""
    try:
        geocaches = Geocache.objects.all().select_related('koordinaten', 'erstellt_von')
        
        # Filtern der Geocaches nach Status (gefunden/nicht gefunden)
        try:
            gefundene_ids = GeocacheFund.objects.filter(nutzer=request.user).values_list('geocache_id', flat=True)
            # Sofort in normale Liste umwandeln, um spätere Datenbankabfragen zu vermeiden
            gefundene_ids = list(gefundene_ids)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting geocache finds: {str(e)}")
            gefundene_ids = []
    except Exception as e:
        # Handle the case where even the Geocache table doesn't exist
        logger = logging.getLogger(__name__)
        logger.error(f"Error accessing Geocache table: {str(e)}")
        geocaches = []
        gefundene_ids = []
    
    return render(request, 'geotune/geocache_liste.html', {
        'geocaches': geocaches,
        'gefundene_ids': gefundene_ids
    })

@login_required
def geocache_detail(request, geocache_id):
    """Detailansicht eines Geocaches"""
    try:
        geocache = get_object_or_404(Geocache, id=geocache_id)
        
        # Prüfen, ob der Nutzer den Geocache bereits gefunden hat
        try:
            already_found = GeocacheFund.objects.filter(nutzer=request.user, geocache=geocache).exists()
            # Anzahl der Finder
            finder_count = geocache.finder.count()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error accessing GeocacheFund table: {str(e)}")
            already_found = False
            finder_count = 0
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error accessing Geocache table: {str(e)}")
        # If we can't find the geocache, redirect to the list
        messages.error(request, "Der angeforderte Geocache konnte nicht gefunden werden.")
        return redirect('geocache_liste')
    
    return render(request, 'geotune/geocache_detail.html', {
        'geocache': geocache,
        'already_found': already_found,
        'finder_count': finder_count
    })

@login_required
def geocache_erstellen(request):
    """Erstellen eines neuen Geocaches"""
    try:
        if request.method == 'POST':
            form = GeocacheForm(request.POST)
            if form.is_valid():
                try:
                    geocache = form.save(commit=False)
                    geocache.erstellt_von = request.user
                    geocache.save()
                    messages.success(request, 'Geocache erfolgreich erstellt!', extra_tags='toast')
                    return redirect('geocache_detail', geocache_id=geocache.id)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error saving Geocache: {str(e)}")
                    messages.error(request, "Fehler beim Speichern des Geocaches. Die Datenbank ist möglicherweise nicht korrekt eingerichtet.", extra_tags='toast')
        else:
            form = GeocacheForm()
        
        return render(request, 'geotune/geocache_form.html', {
            'form': form,
            'is_new': True
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in geocache_erstellen: {str(e)}")
        messages.error(request, "Die Geocache-Funktion ist derzeit nicht verfügbar.", extra_tags='toast')
        return redirect('index')

@login_required
def geocache_bearbeiten(request, geocache_id):
    """Bearbeiten eines bestehenden Geocaches"""
    try:
        geocache = get_object_or_404(Geocache, id=geocache_id)
        
        # Nur der Ersteller darf den Geocache bearbeiten
        if geocache.erstellt_von != request.user:
            messages.error(request, 'Du hast keine Berechtigung, diesen Geocache zu bearbeiten.', extra_tags='toast')
            return redirect('geocache_detail', geocache_id=geocache.id)
        
        if request.method == 'POST':
            form = GeocacheForm(request.POST, instance=geocache)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, 'Geocache erfolgreich aktualisiert!', extra_tags='toast')
                    return redirect('geocache_detail', geocache_id=geocache.id)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error saving Geocache in edit: {str(e)}")
                    messages.error(request, "Fehler beim Speichern des Geocaches.", extra_tags='toast')
        else:
            form = GeocacheForm(instance=geocache)
        
        return render(request, 'geotune/geocache_form.html', {
            'form': form,
            'geocache': geocache,
            'is_new': False
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error accessing Geocache for editing: {str(e)}")
        messages.error(request, "Der angeforderte Geocache konnte nicht bearbeitet werden.", extra_tags='toast')
        return redirect('geocache_liste')

@login_required
def geocache_fund_registrieren(request, geocache_id):
    """Registrieren eines Geocache-Funds"""
    try:
        geocache = get_object_or_404(Geocache, id=geocache_id)
        
        try:
            # Prüfen, ob der Geocache bereits gefunden wurde
            existing_fund = GeocacheFund.objects.filter(nutzer=request.user, geocache=geocache).first()
            
            if existing_fund:
                messages.info(request, f'Du hast diesen Geocache bereits am {existing_fund.funddatum.strftime("%d.%m.%Y")} gefunden.', extra_tags='toast')
            else:
                try:
                    # Neuen Fund registrieren
                    GeocacheFund.objects.create(
                        nutzer=request.user,
                        geocache=geocache,
                        funddatum=timezone.now()
                    )
                    
                    # Gamification-Punkte für den Fund vergeben
                    try:
                        Gamification.objects.create(
                            nutzer=request.user,
                            aktivitaet='geocache_fund',
                            punktewert=10 * geocache.schwierigkeit,  # Punkte basierend auf Schwierigkeit
                            datum=timezone.now(),
                            referenz_id=geocache.id
                        )
                    except Exception as e:
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error creating Gamification entry: {str(e)}")
                        # Continue even if gamification fails
                    
                    messages.success(request, f'Glückwunsch! Du hast den Geocache "{geocache.name}" gefunden!', extra_tags='toast')
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error creating GeocacheFund entry: {str(e)}")
                    messages.error(request, "Es ist ein Fehler beim Registrieren des Funds aufgetreten.", extra_tags='toast')
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking for existing GeocacheFund: {str(e)}")
            messages.error(request, "Die GeocacheFund-Funktion ist derzeit nicht verfügbar.", extra_tags='toast')
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error accessing Geocache with ID {geocache_id}: {str(e)}")
        messages.error(request, "Der angeforderte Geocache konnte nicht gefunden werden.", extra_tags='toast')
    
    return redirect('geocache_detail', geocache_id=geocache_id)