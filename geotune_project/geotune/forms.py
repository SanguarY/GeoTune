# forms.py - Formulare für GeoTune

from django import forms
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, Suche, NutzerGenrePraeferenz,
    SuchePlaylist, PlaylistStandort, Event, Abonnement, Geocache
)
from django.contrib.auth.forms import UserCreationForm

# Gemeinsame Attribute für Form-Widgets
class GeoTuneFormMixin:
    """Basis-Mixin für gemeinsame Widget-Attribute in GeoTune-Formularen"""
    
    @staticmethod
    def get_text_input(placeholder=None, **kwargs):
        """Erzeugt ein standardisiertes TextInput-Widget"""
        attrs = {'class': 'form-control'}
        if placeholder:
            attrs['placeholder'] = placeholder
        attrs.update(kwargs)
        return forms.TextInput(attrs=attrs)
    
    @staticmethod
    def get_textarea_input(rows=3, placeholder=None, **kwargs):
        """Erzeugt ein standardisiertes Textarea-Widget"""
        attrs = {'class': 'form-control', 'rows': rows}
        if placeholder:
            attrs['placeholder'] = placeholder
        attrs.update(kwargs)
        return forms.Textarea(attrs=attrs)
    
    @staticmethod
    def get_checkbox_input(**kwargs):
        """Erzeugt ein standardisiertes Checkbox-Widget"""
        attrs = {'class': 'form-check-input'}
        attrs.update(kwargs)
        return forms.CheckboxInput(attrs=attrs)
    
    @staticmethod
    def get_select_input(**kwargs):
        """Erzeugt ein standardisiertes Select-Widget"""
        attrs = {'class': 'form-select'}
        attrs.update(kwargs)
        return forms.Select(attrs=attrs)
    
    @staticmethod
    def get_checkbox_multiple_input(**kwargs):
        """Erzeugt ein standardisiertes CheckboxSelectMultiple-Widget"""
        attrs = {'class': 'form-check-input'}
        attrs.update(kwargs)
        return forms.CheckboxSelectMultiple(attrs=attrs)

class NutzerCreationForm(UserCreationForm, GeoTuneFormMixin):
    """Formular zur Erstellung neuer Nutzer-Accounts mit erweiterten Feldern"""
    email = forms.EmailField(
        required=True,
        label="E-Mail",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'deine@email.de'
        }),
        error_messages={
            'required': 'Bitte gib deine E-Mail-Adresse ein.',
            'invalid': 'Bitte gib eine gültige E-Mail-Adresse ein.'
        }
    )
    
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        label="Vorname",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dein Vorname'
        })
    )
    
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        label="Nachname",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dein Nachname'
        })
    )
    
    bio = forms.CharField(
        required=False,
        label="Über mich",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Erzähl etwas über dich und deine Musikvorlieben...'
        })
    )
    
    profilbild = forms.ImageField(
        required=False,
        label="Profilbild",
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )
    
    genrevorlieben = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        label="Lieblingsgenres",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'genre-checkbox form-check-input'
        })
    )
    
    error_messages = {
        'password_mismatch': 'Die beiden Passwörter stimmen nicht überein.',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Wähle einen Benutzernamen'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Passwort wählen'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Passwort bestätigen'
        })
        
        # Labels in German
        self.fields['username'].label = "Benutzername"
        self.fields['password1'].label = "Passwort"
        self.fields['password2'].label = "Passwort bestätigen"
        
        # Custom error messages in German
        self.fields['username'].error_messages = {
            'required': 'Bitte gib einen Benutzernamen ein.',
            'unique': 'Dieser Benutzername ist bereits vergeben.',
            'invalid': 'Benutzername enthält ungültige Zeichen.'
        }
        
        self.fields['password1'].error_messages = {
            'required': 'Bitte gib ein Passwort ein.',
        }
        
        self.fields['password2'].error_messages = {
            'required': 'Bitte bestätige dein Passwort.',
        }
    
    class Meta:
        model = Nutzer
        fields = ['username', 'email', 'first_name', 'last_name', 'bio', 'profilbild', 'password1', 'password2', 'genrevorlieben']

class NutzerProfilForm(forms.ModelForm, GeoTuneFormMixin):
    """Form für die Bearbeitung des Nutzerprofils"""
    genrevorlieben = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Bevorzugte Genres"
    )
    
    class Meta:
        model = Nutzer
        fields = ['username', 'email', 'first_name', 'last_name', 'bio', 'profilbild', 'genrevorlieben']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Benutzername'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-Mail-Adresse'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nachname'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Erzähle etwas über dich...'}),
        }
        labels = {
            'username': 'Benutzername',
            'email': 'E-Mail-Adresse',
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'bio': 'Über mich',
            'profilbild': 'Profilbild',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # If the form has an instance, populate the genrevorlieben field with existing preferences
        if instance:
            genre_ids = NutzerGenrePraeferenz.objects.filter(
                nutzer=instance
            ).values_list('genre_id', flat=True)
            
            self.initial['genrevorlieben'] = genre_ids

class PlaylistForm(forms.ModelForm, GeoTuneFormMixin):
    """Formular zum Erstellen und Bearbeiten von Playlists"""
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Genres"
    )
    
    class Meta:
        model = Playlist
        fields = ['name', 'beschreibung', 'ist_oeffentlich', 'genres']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Sommer Hits 2023'
            }),
            'beschreibung': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Beschreibe deine Playlist...'
            }),
            'ist_oeffentlich': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Name',
            'beschreibung': 'Beschreibung',
            'ist_oeffentlich': 'Öffentlich sichtbar'
        }

class LiedForm(forms.ModelForm, GeoTuneFormMixin):
    """Formular zum Hinzufügen und Bearbeiten von Liedern"""
    # Add a dummy plattform field that won't be sent to the database
    plattform = forms.CharField(
        max_length=50,
        required=False, 
        label="Plattform",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. Spotify, YouTube'}),
    )
    
    class Meta:
        model = Lied
        fields = ['titel', 'kuenstler', 'album', 'dauer', 'plattform', 'externe_url', 'cover_bild']
        widgets = {
            'titel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titel des Liedes'}),
            'kuenstler': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Künstler/Band'}),
            'album': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Album (optional)'}),
            'dauer': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Dauer in Sekunden'}),
            'externe_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Link zu Spotify, YouTube etc.'}),
            'cover_bild': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL zum Cover-Bild'}),
        }
        labels = {
            'titel': 'Titel',
            'kuenstler': 'Künstler',
            'album': 'Album',
            'dauer': 'Dauer (Sek.)',
            'externe_url': 'Externer Link',
            'cover_bild': 'Cover-Bild URL'
        }
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Remove plattform from instance to avoid database error
        if hasattr(instance, 'plattform'):
            # Store it temporarily in case we need it elsewhere
            self.plattform_value = instance.plattform
            # Delete the attribute
            delattr(instance, 'plattform')
        if commit:
            instance.save()
        return instance

class StandortForm(forms.ModelForm, GeoTuneFormMixin):
    """Formular zum Erstellen und Bearbeiten von Standorten"""
    class Meta:
        model = Standort
        fields = ['breitengrad', 'laengengrad', 'adresse', 'stadt', 'land', 'beschreibung']
        widgets = {
            'breitengrad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'laengengrad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'stadt': forms.TextInput(attrs={'class': 'form-control'}),
            'land': forms.TextInput(attrs={'class': 'form-control'}),
            'beschreibung': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'breitengrad': 'Breitengrad',
            'laengengrad': 'Längengrad',
            'adresse': 'Adresse',
            'stadt': 'Stadt',
            'land': 'Land',
            'beschreibung': 'Beschreibung'
        }

class GeocacheForm(forms.ModelForm, GeoTuneFormMixin):
    """Formular zum Erstellen und Bearbeiten von Geocaches"""
    class Meta:
        model = Geocache
        fields = ['name', 'beschreibung', 'koordinaten', 'schwierigkeit', 'belohnung']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'beschreibung': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'koordinaten': forms.Select(attrs={'class': 'form-select'}),
            'schwierigkeit': forms.Select(attrs={'class': 'form-select'}),
            'belohnung': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'name': 'Name',
            'beschreibung': 'Beschreibung',
            'koordinaten': 'Standort',
            'schwierigkeit': 'Schwierigkeitsgrad',
            'belohnung': 'Belohnung'
        }
        help_texts = {
            'name': 'Gib deinem Geocache einen passenden Namen',
            'beschreibung': 'Beschreibe den Geocache und gib Hinweise zur Findung',
            'koordinaten': 'Wähle einen bestehenden Standort aus',
            'schwierigkeit': 'Wie schwer ist es, diesen Geocache zu finden?',
            'belohnung': 'Welche Belohnung erhalten Nutzer, die diesen Geocache finden?'
        }

# Neues Event-Formular
class EventForm(forms.ModelForm, GeoTuneFormMixin):
    """Formular zum Erstellen und Bearbeiten von Events"""
    class Meta:
        model = Event
        fields = ['name', 'beschreibung', 'datum', 'ort', 'partner', 'max_teilnehmer', 'bild']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'beschreibung': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'datum': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'ort': forms.Select(attrs={'class': 'form-select'}),
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'max_teilnehmer': forms.NumberInput(attrs={'class': 'form-control'}),
            'bild': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'name': 'Eventname',
            'beschreibung': 'Beschreibung',
            'datum': 'Datum und Uhrzeit',
            'ort': 'Veranstaltungsort',
            'partner': 'Partner/Sponsor (optional)',
            'max_teilnehmer': 'Maximale Teilnehmerzahl (optional)',
            'bild': 'Eventbild (optional)'
        }
        help_texts = {
            'name': 'Gib deinem Event einen aussagekräftigen Namen',
            'beschreibung': 'Beschreibe das Event, den Ablauf und was Teilnehmer erwarten können',
            'datum': 'Wann findet das Event statt?',
            'ort': 'Wo findet das Event statt?',
            'max_teilnehmer': 'Leer lassen für unbegrenzte Teilnehmerzahl'
        }

# Formular zum Hinzufügen von Playlists zu Events
class EventPlaylistForm(forms.Form, GeoTuneFormMixin):
    """Formular zum Hinzufügen von Playlists zu einem Event"""
    playlists = forms.ModelMultipleChoiceField(
        queryset=Playlist.objects.none(),
        required=True,
        label="Playlists auswählen",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Playlists des Nutzers, die noch nicht dem Event zugeordnet sind
            if event:
                self.fields['playlists'].queryset = Playlist.objects.filter(
                    erstellt_von=user
                ).exclude(
                    events=event
                )
            else:
                self.fields['playlists'].queryset = Playlist.objects.filter(erstellt_von=user)

# Abonnement-Formular
class AbonnementForm(forms.ModelForm, GeoTuneFormMixin):
    """Formular zur Auswahl und Verwaltung von Abonnements"""
    class Meta:
        model = Abonnement
        fields = ['abo_typ']
        labels = {
            'abo_typ': 'Abonnement-Typ'
        }
        widgets = {
            'abo_typ': forms.Select(attrs={'class': 'form-select'})
        }
        help_texts = {
            'abo_typ': 'Wähle dein gewünschtes Abonnement-Paket'
        }