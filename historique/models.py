from django.db import models
from fermes.models import Ferme
from moncheptel.models import Animal


class HistoriqueEvenement(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE, related_name='historique_evenements', verbose_name='Ferme')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='historique_evenements', verbose_name='Animal', null=True, blank=True)
    type_evenement = models.CharField(max_length=80, verbose_name='Type d’événement')
    titre = models.CharField(max_length=150, verbose_name='Titre')
    description = models.TextField(blank=True, verbose_name='Description')
    date_evenement = models.DateTimeField(verbose_name='Date événement')
    source_ia = models.BooleanField(default=False, verbose_name='Source IA')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')

    class Meta:
        verbose_name = 'Historique événement'
        verbose_name_plural = 'Historique événements'

    def __str__(self):
        return f'{self.titre} - {self.date_evenement}'
