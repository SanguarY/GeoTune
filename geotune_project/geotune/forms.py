# forms.py - Formulare für GeoTune

from django import forms
from .models import (
    Nutzer, Playlist, Lied, Genre, Standort, Suche
)
from django.contrib.auth.forms import UserCreationForm
from .models import Nutzer

class NutzerCreationForm(UserCreationForm):
    class Meta:
        model = Nutzer
        fields = ['username', 'email', 'password1', 'password2']

class NutzerProfilForm(forms.ModelForm):
    class Meta:
        model = Nutzer
        fields = ['first_name', 'last_name', 'email', 'bio', 'profilbild']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

class PlaylistForm(forms.ModelForm):
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Playlist
        fields = ['name', 'beschreibung', 'ist_oeffentlich', 'genres']
        widgets = {
            'beschreibung': forms.Textarea(attrs={'rows': 3}),
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