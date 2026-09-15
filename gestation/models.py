from django.db import models
from fermes.models import Ferme
from moncheptel.models import Animal


class Gestation(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE, related_name='gestations', verbose_name='Ferme')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='gestations', verbose_name='Animal')
    pere = models.ForeignKey(
        Animal, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gestations_comme_pere', verbose_name='Mâle reproducteur'
    )
    date_debut = models.DateField(verbose_name='Date de saillie')
    date_prevue = models.DateField(verbose_name='Date prévue')
    date_mise_bas_reelle = models.DateField(null=True, blank=True, verbose_name='Date mise bas réelle')
    duree_jours = models.PositiveIntegerField(default=0, verbose_name='Durée estimée (jours)')
    nombre_naissances = models.PositiveIntegerField(null=True, blank=True, verbose_name='Nombre de naissances')
    statut = models.CharField(max_length=60, default='active', verbose_name='Statut')
    note = models.TextField(blank=True, verbose_name='Note')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Date de modification')

    class Meta:
        verbose_name = 'Gestation'
        verbose_name_plural = 'Gestations'

    def __str__(self):
        return f'Gestation - {self.animal}'
