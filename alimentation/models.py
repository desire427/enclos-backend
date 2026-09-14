from django.db import models
from fermes.models import Ferme
from moncheptel.models import Animal


class TypeAliment(models.Model):
    """Types d'aliments créés par l'utilisateur (ex: Foin, Granulés, Ensilage…)."""
    nom         = models.CharField(max_length=120, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Type d\'aliment'
        verbose_name_plural = 'Types d\'aliment'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class FrequenceAlimentation(models.Model):
    """Fréquences d'alimentation créées par l'utilisateur (ex: Quotidienne, Biquotidienne…)."""
    nom         = models.CharField(max_length=120, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fréquence d\'alimentation'
        verbose_name_plural = 'Fréquences d\'alimentation'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Alimentation(models.Model):
    ferme       = models.ForeignKey(
        Ferme, on_delete=models.CASCADE,
        related_name='alimentations', verbose_name='Ferme',
    )
    animal      = models.ForeignKey(
        Animal, on_delete=models.CASCADE,
        related_name='alimentations', verbose_name='Animal',
    )
    type_aliment = models.ForeignKey(
        TypeAliment, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alimentations', verbose_name='Type d\'aliment',
    )
    frequence   = models.ForeignKey(
        FrequenceAlimentation, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alimentations', verbose_name='Fréquence',
    )
    quantite_kg = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='Quantité (kg)',
    )
    date_alimentation = models.DateField(verbose_name='Date alimentation')
    note              = models.TextField(blank=True, verbose_name='Note')
    date_creation     = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True,     verbose_name='Date de modification')

    class Meta:
        verbose_name = 'Alimentation'
        verbose_name_plural = 'Alimentations'
        ordering = ['-date_alimentation']

    def __str__(self):
        type_nom = self.type_aliment.nom if self.type_aliment else '—'
        return f'{self.animal} — {type_nom}'
