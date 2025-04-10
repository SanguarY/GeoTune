# Generated by Django 5.1.6 on 2025-02-25 08:57

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('beschreibung', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Lied',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(max_length=100)),
                ('kuenstler', models.CharField(max_length=100)),
                ('album', models.CharField(blank=True, max_length=100)),
                ('dauer', models.IntegerField()),
                ('externe_url', models.URLField(blank=True)),
                ('cover_bild', models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Standort',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('breitengrad', models.FloatField()),
                ('laengengrad', models.FloatField()),
                ('adresse', models.CharField(blank=True, max_length=255)),
                ('stadt', models.CharField(blank=True, max_length=100)),
                ('land', models.CharField(blank=True, max_length=100)),
                ('beschreibung', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Nutzer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('bio', models.TextField(blank=True)),
                ('profilbild', models.ImageField(blank=True, null=True, upload_to='profile_pics/')),
                ('premium_status', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='NutzerSucheTeilnahme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beitrittsdatum', models.DateTimeField(default=django.utils.timezone.now)),
                ('fortschritt', models.IntegerField(default=0)),
                ('abgeschlossen', models.BooleanField(default=False)),
                ('nutzer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('beschreibung', models.TextField(blank=True)),
                ('erstellungsdatum', models.DateTimeField(default=django.utils.timezone.now)),
                ('ist_oeffentlich', models.BooleanField(default=True)),
                ('anzahl_aufrufe', models.IntegerField(default=0)),
                ('erstellt_von', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='erstellte_playlists', to=settings.AUTH_USER_MODEL)),
                ('genres', models.ManyToManyField(related_name='playlists', to='geotune.genre')),
            ],
        ),
        migrations.CreateModel(
            name='PlaylistLied',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum_hinzugefuegt', models.DateTimeField(default=django.utils.timezone.now)),
                ('hinzugefuegt_von', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('lied', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.lied')),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.playlist')),
            ],
            options={
                'unique_together': {('playlist', 'lied')},
            },
        ),
        migrations.AddField(
            model_name='lied',
            name='playlists',
            field=models.ManyToManyField(related_name='lieder', through='geotune.PlaylistLied', to='geotune.playlist'),
        ),
        migrations.CreateModel(
            name='PlaylistStandort',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gueltig_von', models.DateTimeField(default=django.utils.timezone.now)),
                ('gueltig_bis', models.DateTimeField(blank=True, null=True)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.playlist')),
                ('standort', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.standort')),
            ],
            options={
                'unique_together': {('playlist', 'standort')},
            },
        ),
        migrations.AddField(
            model_name='playlist',
            name='standorte',
            field=models.ManyToManyField(related_name='playlists', through='geotune.PlaylistStandort', to='geotune.standort'),
        ),
        migrations.CreateModel(
            name='Suche',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('beschreibung', models.TextField(blank=True)),
                ('startdatum', models.DateField()),
                ('enddatum', models.DateField(blank=True, null=True)),
                ('erstellt_von', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='erstellte_suchen', to=settings.AUTH_USER_MODEL)),
                ('teilnehmer', models.ManyToManyField(related_name='teilgenommene_suchen', through='geotune.NutzerSucheTeilnahme', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='nutzersucheteilnahme',
            name='suche',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.suche'),
        ),
        migrations.CreateModel(
            name='SuchePlaylist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reihenfolge_nummer', models.IntegerField()),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.playlist')),
                ('suche', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.suche')),
            ],
            options={
                'unique_together': {('suche', 'playlist')},
            },
        ),
        migrations.AddField(
            model_name='suche',
            name='playlists',
            field=models.ManyToManyField(related_name='suchen', through='geotune.SuchePlaylist', to='geotune.playlist'),
        ),
        migrations.CreateModel(
            name='NutzerGenrePraeferenz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('praeferenzlevel', models.IntegerField()),
                ('genre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.genre')),
                ('nutzer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='genre_praeferenzen', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('nutzer', 'genre')},
            },
        ),
        migrations.CreateModel(
            name='NutzerVerbindung',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('erstellungsdatum', models.DateField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('angefragt', 'Angefragt'), ('akzeptiert', 'Akzeptiert'), ('blockiert', 'Blockiert')], default='angefragt', max_length=20)),
                ('nutzer1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gesendete_verbindungen', to=settings.AUTH_USER_MODEL)),
                ('nutzer2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='erhaltene_verbindungen', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('nutzer1', 'nutzer2')},
            },
        ),
        migrations.CreateModel(
            name='NutzerPlaylistInteraktion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ist_favorit', models.BooleanField(default=False)),
                ('letzter_besuch', models.DateTimeField(blank=True, null=True)),
                ('besuchszaehler', models.IntegerField(default=0)),
                ('nutzer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='geotune.playlist')),
            ],
            options={
                'unique_together': {('nutzer', 'playlist')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='nutzersucheteilnahme',
            unique_together={('nutzer', 'suche')},
        ),
    ]
