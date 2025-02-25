from django.core.management.base import BaseCommand
from geotune.models import Genre, Nutzer, Standort, Playlist, Lied, PlaylistLied # type: ignore
from django.contrib.auth.hashers import make_password
import random
from django.utils import timezone

class Command(BaseCommand):
    help = 'Lädt Testdaten für GeoTune'
    
    def handle(self, *args, **options):
        self.stdout.write('Lade Testdaten...')
        
        # Genres erstellen
        genre_names = [
            'Pop', 'Rock', 'Hip-Hop', 'Jazz', 'Elektronische Musik',
            'Klassik', 'R&B', 'Country', 'Reggae', 'Metal'
        ]
        
        genres = []
        for genre_name in genre_names:
            genre, created = Genre.objects.get_or_create(name=genre_name)
            genres.append(genre)
            if created:
                self.stdout.write(f'Genre "{genre_name}" erstellt')
        
        # Testnutzer erstellen
        test_user, created = Nutzer.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'password': make_password('testpassword123'),
                'is_staff': True
            }
        )
        if created:
            self.stdout.write('Testnutzer erstellt')
        
        # Standorte in Mannheim erstellen
        mannheim_locations = [
            {'name': 'Wasserturm', 'lat': 49.4836, 'lng': 8.4731},
            {'name': 'Schloss', 'lat': 49.4836, 'lng': 8.4630},
            {'name': 'Universität', 'lat': 49.4833, 'lng': 8.4635},
            {'name': 'Marktplatz', 'lat': 49.4872, 'lng': 8.4654},
            {'name': 'DHBW', 'lat': 49.4789, 'lng': 8.4756}
        ]
        
        standorte = []
        for loc in mannheim_locations:
            standort, created = Standort.objects.get_or_create(
                breitengrad=loc['lat'],
                laengengrad=loc['lng'],
                defaults={
                    'beschreibung': f"Standort bei {loc['name']}",
                    'stadt': 'Mannheim',
                    'land': 'Deutschland'
                }
            )
            standorte.append(standort)
            if created:
                self.stdout.write(f'Standort bei {loc["name"]} erstellt')
        
        # Beispiel-Lieder
        lieder_data = [
            {'titel': 'Imagination', 'kuenstler': 'Hans Zimmer', 'album': 'Inception'},
            {'titel': 'Thunderstruck', 'kuenstler': 'AC/DC', 'album': 'The Razors Edge'},
            {'titel': 'Bohemian Rhapsody', 'kuenstler': 'Queen', 'album': 'A Night at the Opera'},
            {'titel': 'Shape of You', 'kuenstler': 'Ed Sheeran', 'album': '÷'},
            {'titel': 'Smells Like Teen Spirit', 'kuenstler': 'Nirvana', 'album': 'Nevermind'},
            {'titel': 'Billie Jean', 'kuenstler': 'Michael Jackson', 'album': 'Thriller'},
            {'titel': 'Stairway to Heaven', 'kuenstler': 'Led Zeppelin', 'album': 'Led Zeppelin IV'},
            {'titel': 'Imagine', 'kuenstler': 'John Lennon', 'album': 'Imagine'},
            {'titel': 'Sweet Child O Mine', 'kuenstler': 'Guns N Roses', 'album': 'Appetite for Destruction'},
            {'titel': 'Like a Rolling Stone', 'kuenstler': 'Bob Dylan', 'album': 'Highway 61 Revisited'}
        ]
        
        lieder = []
        for lied_data in lieder_data:
            lied, created = Lied.objects.get_or_create(
                titel=lied_data['titel'],
                kuenstler=lied_data['kuenstler'],
                defaults={
                    'album': lied_data['album'],
                    'dauer': random.randint(180, 300)  # 3-5 Minuten
                }
            )
            lieder.append(lied)
            if created:
                self.stdout.write(f'Lied "{lied_data["titel"]}" erstellt')
        
        # Beispiel-Playlists
        playlist_names = [
            'Mannheim Classics', 'Entspannungsmusik', 'Workout Hits',
            'Party Musik', 'Konzentration & Fokus'
        ]
        
        for i, name in enumerate(playlist_names):
            playlist, created = Playlist.objects.get_or_create(
                name=name,
                erstellt_von=test_user,
                defaults={
                    'beschreibung': f'Eine tolle Playlist mit {name}',
                    'erstellungsdatum': timezone.now(),
                    'ist_oeffentlich': True
                }
            )
            
            if created:
                self.stdout.write(f'Playlist "{name}" erstellt')
                
                # Standort zuweisen
                standort = standorte[i % len(standorte)]
                playlist.standorte.add(standort, through_defaults={'gueltig_von': timezone.now()})
                
                # Genres zuweisen (2 zufällige)
                selected_genres = random.sample(genres, 2)
                playlist.genres.add(*selected_genres)
                
                # Lieder zuweisen (3-5 zufällige)
                selected_lieder = random.sample(lieder, random.randint(3, 5))
                for lied in selected_lieder:
                    PlaylistLied.objects.create(
                        playlist=playlist,
                        lied=lied,
                        hinzugefuegt_von=test_user,
                        datum_hinzugefuegt=timezone.now()
                    )
        
        self.stdout.write(self.style.SUCCESS('Testdaten erfolgreich geladen!'))