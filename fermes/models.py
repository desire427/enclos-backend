from django.conf import settings
from django.db import models


class Ferme(models.Model):
    nom = models.CharField(max_length=120, verbose_name='Nom de la ferme')
    localisation = models.CharField(max_length=150, blank=True, verbose_name='Localisation')
    superficie = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Superficie (ha)')
    coordonnees_gps = models.CharField(max_length=120, blank=True, verbose_name='Coordonnées GPS')
    description = models.TextField(blank=True, verbose_name='Description')
    proprietaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fermes', verbose_name='Propriétaire')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')

    class Meta:
        verbose_name = 'Ferme'
        verbose_name_plural = 'Fermes'

    def __str__(self):
        return self.nom
