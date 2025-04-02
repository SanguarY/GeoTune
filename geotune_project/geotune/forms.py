# forms.py - Formulare für GeoTune

from django import forms
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, Suche
)
from django.contrib.auth.forms import UserCreationForm
from .models import Nutzer

class NutzerCreationForm(UserCreationForm):
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

class NutzerProfilForm(forms.ModelForm):
    genrevorlieben = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        label="Lieblingsgenres",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'genre-checkbox form-check-input'
        })
    )
    
    class Meta:
        model = Nutzer
        fields = ['first_name', 'last_name', 'email', 'bio', 'profilbild']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vorname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nachname'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-Mail-Adresse'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Erzähle etwas über dich...'}),
            'profilbild': forms.FileInput(attrs={'class': 'form-control d-none'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Vorausgewählte Genres aus den Nutzerpräferenzen laden
        if self.instance and self.instance.pk:
            self.initial['genrevorlieben'] = self.instance.genre_praeferenzen.values_list('genre', flat=True)

class PlaylistForm(forms.ModelForm):
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False
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

class LiedForm(forms.ModelForm):
    class Meta:
        model = Lied
        fields = ['titel', 'kuenstler', 'album', 'dauer', 'externe_url', 'cover_bild']
        widgets = {
            'dauer': forms.NumberInput(attrs={'placeholder': 'Dauer in Sekunden'}),
            'externe_url': forms.URLInput(attrs={'placeholder': 'Link zu Spotify, YouTube etc.'}),
            'cover_bild': forms.URLInput(attrs={'placeholder': 'URL zum Cover-Bild'}),
        }

class StandortForm(forms.ModelForm):
    class Meta:
        model = Standort
        fields = ['breitengrad', 'laengengrad', 'adresse', 'stadt', 'land', 'beschreibung']
        widgets = {
            'beschreibung': forms.Textarea(attrs={'rows': 2}),
            'breitengrad': forms.NumberInput(attrs={'step': '0.000001'}),
            'laengengrad': forms.NumberInput(attrs={'step': '0.000001'}),
        }

class SucheForm(forms.ModelForm):
    class Meta:
        model = Suche
        fields = ['name', 'beschreibung', 'startdatum', 'enddatum']
        widgets = {
            'beschreibung': forms.Textarea(attrs={'rows': 3}),
            'startdatum': forms.DateInput(attrs={'type': 'date'}),
            'enddatum': forms.DateInput(attrs={'type': 'date', 'required': False}),
        }