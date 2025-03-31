# views.py - Definition der Views für GeoTune

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, 
    NutzerVerbindung, PlaylistLied, Suche,
    NutzerPlaylistInteraktion, SuchePlaylist, NutzerSucheTeilnahme, 
    NutzerGenrePraeferenz, PlaylistStandort
)
from .forms import (
    PlaylistForm, LiedForm, NutzerProfilForm,
    StandortForm, SucheForm
)
from .forms import NutzerCreationForm
import json
from math import radians, cos, sin, asin, sqrt

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
            form.save()
            messages.success(request, 'Profil erfolgreich aktualisiert!')
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
            
            messages.success(request, 'Playlist erfolgreich erstellt!')
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
            PlaylistLied.objects.create(
                playlist=playlist,
                lied=lied,
                hinzugefuegt_von=request.user
            )
            messages.success(request, 'Lied erfolgreich hinzugefügt!')
            return redirect('playlist_detail', playlist_id=playlist.id)
    else:
        lied_form = LiedForm()
    
    # Standorte abrufen
    standorte = PlaylistStandort.objects.filter(playlist=playlist).select_related('standort') # type: ignore
    
    return render(request, 'geotune/playlist_detail.html', {
        'playlist': playlist,
        'lieder': lieder,
        'lied_form': lied_form,
        'standorte': standorte,
        'ist_favorit': interaktion.ist_favorit
    })

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
            
            messages.success(request, 'Standort erfolgreich hinzugefügt!')
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
    """Neue Playlist-Suche erstellen"""
    if request.method == 'POST':
        form = SucheForm(request.POST)
        if form.is_valid():
            suche = form.save(commit=False)
            suche.erstellt_von = request.user
            suche.save()
            
            # Playlists hinzufügen
            playlist_ids = request.POST.getlist('playlists')
            
            for i, playlist_id in enumerate(playlist_ids):
                SuchePlaylist.objects.create( # type: ignore
                    suche=suche,
                    playlist_id=int(playlist_id),
                    reihenfolge_nummer=i+1
                )
            
            messages.success(request, 'Playlist-Suche erfolgreich erstellt!')
            return redirect('suche_detail', suche_id=suche.id)
    else:
        form = SucheForm()
    
    # Eigene Playlists des Nutzers für die Auswahl anzeigen
    eigene_playlists = Playlist.objects.filter(erstellt_von=request.user)
    
    return render(request, 'geotune/suche_form.html', {
        'form': form,
        'eigene_playlists': eigene_playlists
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
    
    # Verbundene Nutzer herausfiltern
    empfohlene_nutzer = aehnliche_nutzer.exclude(id__in=verbundene_ids)
    
    return render(request, 'geotune/nutzer_empfehlungen.html', {
        'empfohlene_nutzer': empfohlene_nutzer
    })

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

def register(request):
    """Registrierung für neue Nutzer"""
    if request.method == 'POST':
        form = NutzerCreationForm(request.POST)  # Benutzen Sie das neue Formular
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registrierung erfolgreich!')
            return redirect('index')
    else:
        form = NutzerCreationForm()  # Benutzen Sie das neue Formular
    
    return render(request, 'geotune/registration/register.html', {'form': form})

def custom_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('index')