# models.py - Definition der Datenmodelle für GeoTune

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Nutzer(AbstractUser):
    bio = models.TextField(blank=True)
    profilbild = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    premium_status = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    beschreibung = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Standort(models.Model):
    breitengrad = models.FloatField()
    laengengrad = models.FloatField()
    adresse = models.CharField(max_length=255, blank=True)
    stadt = models.CharField(max_length=100, blank=True)
    land = models.CharField(max_length=100, blank=True)
    beschreibung = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.stadt}, {self.land} ({self.breitengrad}, {self.laengengrad})"

class Playlist(models.Model):
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

class Lied(models.Model):
    titel = models.CharField(max_length=100)
    kuenstler = models.CharField(max_length=100)
    album = models.CharField(max_length=100, blank=True)
    dauer = models.IntegerField()  # in Sekunden
    externe_url = models.URLField(blank=True)
    cover_bild = models.URLField(blank=True)
    playlists = models.ManyToManyField(Playlist, through='PlaylistLied', related_name='lieder')
    
    def __str__(self):
        return f"{self.titel} - {self.kuenstler}"

class PlaylistLied(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    lied = models.ForeignKey(Lied, on_delete=models.CASCADE)
    hinzugefuegt_von = models.ForeignKey(Nutzer, on_delete=models.SET_NULL, null=True)
    datum_hinzugefuegt = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('playlist', 'lied')

class PlaylistStandort(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    standort = models.ForeignKey(Standort, on_delete=models.CASCADE)
    gueltig_von = models.DateTimeField(default=timezone.now)
    gueltig_bis = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('playlist', 'standort')

class NutzerVerbindung(models.Model):
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
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE, related_name='genre_praeferenzen')
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    praeferenzlevel = models.IntegerField()  # 1-10
    
    class Meta:
        unique_together = ('nutzer', 'genre')

class Suche(models.Model):
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
    suche = models.ForeignKey(Suche, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    reihenfolge_nummer = models.IntegerField()
    
    class Meta:
        unique_together = ('suche', 'playlist')

class NutzerSucheTeilnahme(models.Model):
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE)
    suche = models.ForeignKey(Suche, on_delete=models.CASCADE)
    beitrittsdatum = models.DateTimeField(default=timezone.now)
    fortschritt = models.IntegerField(default=0)
    abgeschlossen = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('nutzer', 'suche')

class NutzerPlaylistInteraktion(models.Model):
    nutzer = models.ForeignKey(Nutzer, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    ist_favorit = models.BooleanField(default=False)
    letzter_besuch = models.DateTimeField(null=True, blank=True)
    besuchszaehler = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('nutzer', 'playlist')