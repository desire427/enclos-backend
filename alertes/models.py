from django.db import models
from fermes.models import Ferme
from moncheptel.models import Animal


class Alerte(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE, related_name='alertes', verbose_name='Ferme')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='alertes', verbose_name='Animal', null=True, blank=True)
    type_alerte = models.CharField(max_length=80, verbose_name='Type d’alerte')
    message = models.TextField(verbose_name='Message')
    statut = models.CharField(max_length=60, default='non_lue', verbose_name='Statut')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Date de modification')

    class Meta:
        verbose_name = 'Alerte'
        verbose_name_plural = 'Alertes'

    def __str__(self):
        return f'{self.type_alerte} - {self.statut}'
