from django.db import models


class Plan(models.Model):
    nom = models.CharField(max_length=100, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    prix = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prix')
    duree_mois = models.IntegerField(default=1, verbose_name='Durée en mois')
    nb_fermes_max = models.IntegerField(default=1, verbose_name='Nombre maximum de fermes')
    nb_animaux_max = models.IntegerField(default=50, verbose_name='Nombre maximum d’animaux')
    acces_ia = models.BooleanField(default=False, verbose_name='Accès IA')
    acces_support = models.BooleanField(default=False, verbose_name='Accès support')
    acces_analyses = models.BooleanField(default=False, verbose_name='Accès analyses')

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'

    def __str__(self):
        return self.nom
