# models.py - Definition der Datenmodelle für GeoTune

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Nutzer(AbstractUser):
    """
    Erweitertes Nutzermodell mit zusätzlichen Profilinformationen.
    Basiert auf dem Django-AbstractUser für Authentifizierung.
    """
    bio = models.TextField(blank=True)
    profilbild = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    premium_status = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username

class Genre(models.Model):
    """Musikgenres für Playlists und Nutzer-Präferenzen."""
    name = models.CharField(max_length=50, unique=True)
    beschreibung = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Standort(models.Model):
    """
    Geographische Standorte für Playlists, Events und Geocaches.
    Speichert Koordinaten und Adressinformationen.
    """
    breitengrad = models.FloatField()
    laengengrad = models.FloatField()
    adresse = models.CharField(max_length=255, blank=True)
    stadt = models.CharField(max_length=100, blank=True)
    land = models.CharField(max_length=100, blank=True)
    beschreibung = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.stadt}, {self.land} ({self.breitengrad}, {self.laengengrad})"

# Neues Abonnement-Modell
class Abonnement(models.Model):
    """
    Abonnement-Modell für verschiedene Mitgliedschaftsstufen.
    Beeinflusst den Premium-Status des Nutzers.
    """
    ABO_TYPEN = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('pro', 'Professional')
    ]
    
    nutzer = models.OneToOneField(Nutzer, on_delete=models.CASCADE, related_name='abonnement')
    abo_typ = models.CharField(max_length=20, choices=ABO_TYPEN, default='basic')
    preis = models.DecimalField(max_digits=6, decimal_places=2)
    startdatum = models.DateField(default=timezone.now)
    enddatum = models.DateField(null=True, blank=True)
    aktiv = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nutzer.username} - {self.abo_typ}"
    
    def save(self, *args, **kwargs):
        """Überschriebene save-Methode, die den Premium-Status des Nutzers aktualisiert."""
        # Aktualisiere den premium_status des Nutzers basierend auf dem Abo-Typ
        if self.abo_typ in ['premium', 'pro'] and self.aktiv:
            self.nutzer.premium_status = True
            self.nutzer.save()
        else:
            # Wenn das Abo nicht premium/pro oder nicht aktiv ist, setze premium_status auf False
            self.nutzer.premium_status = False
            self.nutzer.save()
        super().save(*args, **kwargs)

# Neues Gamification-Modell
class Gamification(models.Model):
    """
    Gamification-System zur Belohnung von Nutzeraktivitäten.
    Tracking von Punkten für verschiedene Aktionen.
    """
    AKTIVITAETEN = [
        ('anmeldung', 'Tägliche Anmeldung'),
        ('playlist_erstellen', 'Playlist erstellen'),
        ('kommentar', 'Kommentar schreiben'),
        ('freund_einladen', 'Freund einladen'),
        ('event_teilnahme', 'Event-Teilnahme'),
        ('geocache_fund', 'Geocache gefunden')
    ]
    
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='punkte')
    aktivitaet = models.CharField(max_length=50, choices=AKTIVITAETEN)
    punktewert = models.IntegerField()
    datum = models.DateTimeField(default=timezone.now)
    referenz_id = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nutzer.username} - {self.aktivitaet} (+{self.punktewert})"
    
    class Meta:
        ordering = ['-datum']

# Neues Partner-Modell
class Partner(models.Model):
    """
    Partner-Organisationen für Kooperationen, Sponsoring und Werbung.
    Können mit Events verknüpft werden.
    """
    PARTNER_TYPEN = [
        ('sponsor', 'Sponsor'),
        ('werbekunde', 'Werbekunde'),
        ('kooperation', 'Kooperationspartner')
    ]
    
    name = models.CharField(max_length=100)
    typ = models.CharField(max_length=20, choices=PARTNER_TYPEN)
    kontakt = models.EmailField()
    telefon = models.CharField(max_length=20, blank=True)
    kooperationsbeginn = models.DateField()
    kooperationsende = models.DateField(null=True, blank=True)
    logo = models.ImageField(upload_to='partner_logos/', blank=True, null=True)
    beschreibung = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_typ_display()})"
    
    class Meta:
        verbose_name_plural = "Partner"

class Playlist(models.Model):
    """
    Zentrale Playlist-Entität, die Lieder an Standorten sammelt.
    Kann mit Genres und Standorten verknüpft werden.
    """
    name = models.CharField(max_length=100)
    beschreibung = models.TextField(blank=True)
    erstellungsdatum = models.DateTimeField(default=timezone.now)
    erstellt_von = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='erstellte_playlists')
    ist_oeffentlich = models.BooleanField(default=True)
    anzahl_aufrufe = models.IntegerField(default=0)
    genres = models.ManyToManyField(Genre, related_name='playlists')
    standorte = models.ManyToManyField(Standort, through='PlaylistStandort', related_name='playlists')
    
    def __str__(self):
        return self.name

# Neues Event-Modell
class Event(models.Model):
    """
    Event-Modell für musikbezogene Veranstaltungen.
    Kann Playlists und Partner zugeordnet haben.
    """
    name = models.CharField(max_length=100)
    beschreibung = models.TextField()
    datum = models.DateTimeField()
    ort = models.ForeignKey(Standort, on_delete=models.CASCADE, related_name='events')
    erstellt_von = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='erstellte_events')
    teilnehmer = models.ManyToManyField(Nutzer, related_name='teilgenommene_events')
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True, related_name='gesponserte_events')
    playlists = models.ManyToManyField(Playlist, related_name='events', blank=True)
    bild = models.ImageField(upload_to='event_images/', blank=True, null=True)
    max_teilnehmer = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.datum.strftime('%d.%m.%Y')})"
    
    class Meta:
        ordering = ['datum']

class Lied(models.Model):
    """
    Musikstück-Modell mit Metadaten und Links zu Streaming-Plattformen.
    Wird über PlaylistLied mit Playlists verbunden.
    """
    titel = models.CharField(max_length=100)
    kuenstler = models.CharField(max_length=100)
    album = models.CharField(max_length=100, blank=True)
    dauer = models.IntegerField()  # in Sekunden
    plattform = models.CharField(max_length=50, blank=True)  # z.B. Spotify, YouTube, Apple Music
    streaming_link = models.URLField(blank=True)
    externe_url = models.URLField(blank=True)
    cover_bild = models.URLField(blank=True)
    playlists = models.ManyToManyField(Playlist, through='PlaylistLied', related_name='lieder')
    
    def __str__(self):
        return f"{self.titel} - {self.kuenstler}"

class PlaylistLied(models.Model):
    """Verknüpfungstabelle zwischen Playlist und Lied mit zusätzlichen Metadaten."""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    lied = models.ForeignKey(Lied, on_delete=models.CASCADE)
    hinzugefuegt_von = models.ForeignKey(Nutzer, on_delete=models.SET_NULL, null=True)
    datum_hinzugefuegt = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('playlist', 'lied')

class PlaylistStandort(models.Model):
    """Verknüpfungstabelle zwischen Playlist und Standort mit Gültigkeitszeitraum."""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    standort = models.ForeignKey(Standort, on_delete=models.CASCADE)
    gueltig_von = models.DateTimeField(default=timezone.now)
    gueltig_bis = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('playlist', 'standort')

class NutzerVerbindung(models.Model):
    """
    Freundschafts-/Verbindungssystem zwischen Nutzern.
    Unterstützt Anfragen, Akzeptieren und Blockieren.
    """
    STATUS_CHOICES = [
        ('angefragt', 'Angefragt'),
        ('akzeptiert', 'Akzeptiert'),
        ('blockiert', 'Blockiert'),
    ]
    
    nutzer1 = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='gesendete_verbindungen')
    nutzer2 = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='erhaltene_verbindungen')
    erstellungsdatum = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='angefragt')
    
    class Meta:
        unique_together = ('nutzer1', 'nutzer2')

class NutzerGenrePraeferenz(models.Model):
    """Verknüpfungstabelle für die Musikvorlieben eines Nutzers mit Präferenzstärke."""
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='genre_praeferenzen')
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    praeferenzlevel = models.IntegerField()  # 1-10
    
    class Meta:
        unique_together = ('nutzer', 'genre')

class Suche(models.Model):
    """
    Modell für geführte Entdeckungstouren mit mehreren Playlists.
    Kann als Musikschnitzeljagd verwendet werden.
    """
    name = models.CharField(max_length=100)
    beschreibung = models.TextField(blank=True)
    startdatum = models.DateField()
    enddatum = models.DateField(null=True, blank=True)
    erstellt_von = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='erstellte_suchen')
    playlists = models.ManyToManyField(Playlist, through='SuchePlaylist', related_name='suchen')
    teilnehmer = models.ManyToManyField(Nutzer, through='NutzerSucheTeilnahme', related_name='teilgenommene_suchen')
    
    def __str__(self):
        return self.name

class SuchePlaylist(models.Model):
    """Verbindungstabelle zwischen Suche und Playlist mit definierter Reihenfolge."""
    suche = models.ForeignKey(Suche, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    reihenfolge_nummer = models.IntegerField()
    
    class Meta:
        unique_together = ('suche', 'playlist')

class NutzerSucheTeilnahme(models.Model):
    """Speichert den Fortschritt eines Nutzers bei einer Suche/Tour."""
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE)
    suche = models.ForeignKey(Suche, on_delete=models.CASCADE)
    beitrittsdatum = models.DateTimeField(default=timezone.now)
    fortschritt = models.IntegerField(default=0)
    abgeschlossen = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('nutzer', 'suche')

class NutzerPlaylistInteraktion(models.Model):
    """Speichert Interaktionen eines Nutzers mit einer Playlist (Favoriten, Besuche)."""
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    ist_favorit = models.BooleanField(default=False)
    letzter_besuch = models.DateTimeField(null=True, blank=True)
    besuchszaehler = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('nutzer', 'playlist')

class Kommentar(models.Model):
    """Nutzerkommentare zu Playlists."""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='kommentare')
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='kommentare')
    text = models.TextField()
    erstellungsdatum = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-erstellungsdatum']
    
    def __str__(self):
        return f"Kommentar von {self.nutzer.username} zu {self.playlist.name}"

class Geocache(models.Model):
    """
    Geocache-Modell für standortbezogene Schatzsuchen.
    Teil des Gamification-Systems zur Entdeckung neuer Orte.
    """
    SCHWIERIGKEITEN = [
        (1, 'Sehr einfach'),
        (2, 'Einfach'),
        (3, 'Mittel'),
        (4, 'Schwer'),
        (5, 'Sehr schwer')
    ]
    
    name = models.CharField(max_length=100)
    beschreibung = models.TextField()
    koordinaten = models.ForeignKey(Standort, on_delete=models.CASCADE, related_name='geocaches')
    schwierigkeit = models.IntegerField(choices=SCHWIERIGKEITEN, default=3)
    belohnung = models.CharField(max_length=255, blank=True)
    erstellt_von = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='erstellte_geocaches')
    finder = models.ManyToManyField(Nutzer, through='GeocacheFund', related_name='gefundene_geocaches')
    
    def __str__(self):
        return f"{self.name} (Schwierigkeit: {self.get_schwierigkeit_display()})"

class GeocacheFund(models.Model):
    """Verknüpfungstabelle, die den Fund eines Geocaches durch einen Nutzer protokolliert."""
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE)
    geocache = models.ForeignKey(Geocache, on_delete=models.CASCADE)
    funddatum = models.DateTimeField(default=timezone.now)
    bewertung = models.IntegerField(null=True, blank=True)
    kommentar = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('nutzer', 'geocache')
        verbose_name_plural = "Geocache Funde"
    
    def __str__(self):
        return f"{self.nutzer.username} hat {self.geocache.name} gefunden am {self.funddatum.strftime('%d.%m.%Y')}"