# Generated by Django 4.2.20 on 2025-04-02 23:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('geotune', '0004_kommentar_delete_playlistkommentar'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('typ', models.CharField(choices=[('sponsor', 'Sponsor'), ('werbekunde', 'Werbekunde'), ('kooperation', 'Kooperationspartner')], max_length=20)),
                ('kontakt', models.EmailField(max_length=254)),
                ('telefon', models.CharField(blank=True, max_length=20)),
                ('kooperationsbeginn', models.DateField()),
                ('kooperationsende', models.DateField(blank=True, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='partner_logos/')),
                ('beschreibung', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'Partner',
            },
        ),
        migrations.CreateModel(
            name='Gamification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aktivitaet', models.CharField(choices=[('anmeldung', 'Tägliche Anmeldung'), ('playlist_erstellen', 'Playlist erstellen'), ('kommentar', 'Kommentar schreiben'), ('freund_einladen', 'Freund einladen'), ('event_teilnahme', 'Event-Teilnahme')], max_length=50)),
                ('punktewert', models.IntegerField()),
                ('datum', models.DateTimeField(default=django.utils.timezone.now)),
                ('nutzer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='punkte', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-datum'],
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('beschreibung', models.TextField()),
                ('datum', models.DateTimeField()),
                ('bild', models.ImageField(blank=True, null=True, upload_to='event_images/')),
                ('max_teilnehmer', models.IntegerField(blank=True, null=True)),
                ('erstellt_von', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='erstellte_events', to=settings.AUTH_USER_MODEL)),
                ('ort', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='geotune.standort')),
                ('partner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gesponserte_events', to='geotune.partner')),
                ('playlists', models.ManyToManyField(blank=True, related_name='events', to='geotune.playlist')),
                ('teilnehmer', models.ManyToManyField(related_name='teilgenommene_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['datum'],
            },
        ),
        migrations.CreateModel(
            name='Abonnement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abo_typ', models.CharField(choices=[('basic', 'Basic'), ('premium', 'Premium'), ('pro', 'Professional')], default='basic', max_length=20)),
                ('preis', models.DecimalField(decimal_places=2, max_digits=6)),
                ('startdatum', models.DateField(default=django.utils.timezone.now)),
                ('enddatum', models.DateField(blank=True, null=True)),
                ('aktiv', models.BooleanField(default=True)),
                ('nutzer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='abonnement', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
