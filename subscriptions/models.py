from django.conf import settings
from django.db import models

from plans.models import Plan


class Subscription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'pending'),
        ('active', 'active'),
        ('expired', 'expired'),
        ('cancelled', 'cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions', null=True, blank=True, verbose_name='Utilisateur')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions', verbose_name='Plan')
    date_debut = models.DateTimeField(auto_now_add=True, verbose_name='Date de début')
    date_fin = models.DateTimeField(null=True, blank=True, verbose_name='Date de fin')
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Statut')
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Montant payé')
    date_paiement = models.DateTimeField(null=True, blank=True, verbose_name='Date de paiement')
    paydunya_token = models.CharField(max_length=120, blank=True, unique=True, null=True, verbose_name='Token PayDunya')
    receipt_url = models.URLField(blank=True, verbose_name='URL du reçu PayDunya')
    moyen_paiement = models.CharField(max_length=50, blank=True, verbose_name='Moyen de paiement')
    inscription_en_attente = models.JSONField(default=dict, blank=True, verbose_name='Inscription en attente')

    class Meta:
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'

    def __str__(self):
        return f'{self.user} - {self.plan}'
