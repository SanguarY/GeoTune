# Generated by Django 4.2.20 on 2025-04-03 01:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geotune', '0005_partner_gamification_event_abonnement'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamification',
            name='referenz_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
