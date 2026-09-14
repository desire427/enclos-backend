from django.db import models
from moncheptel.models import Animal


class PredictionResultat(models.Model):
    """Stocke chaque résultat de prédiction IA pour un animal."""

    DECLENCHEUR_CHOICES = [
        ('alimentation', 'Alimentation'),
        ('sante',        'Suivi santé'),
        ('manuel',       'Manuel'),
    ]

    animal        = models.ForeignKey(
        Animal, on_delete=models.CASCADE,
        related_name='predictions', verbose_name='Animal',
    )
    declencheur   = models.CharField(
        max_length=20, choices=DECLENCHEUR_CHOICES,
        default='manuel', verbose_name='Déclencheur',
    )
    est_malade    = models.BooleanField(verbose_name='Prédit malade')
    probabilite   = models.FloatField(verbose_name='Probabilité maladie')
    shap_values   = models.JSONField(verbose_name='Valeurs SHAP', default=dict)
    features_used = models.JSONField(verbose_name='Features utilisées', default=dict)
    comparaison_historique = models.JSONField(verbose_name='Comparaison à l’historique', default=dict)
    explication_llm = models.TextField(blank=True, verbose_name='Explication LLM')
    envoye_n8n    = models.BooleanField(default=False, verbose_name='Envoyé à n8n')
    date_prediction = models.DateTimeField(auto_now_add=True, verbose_name='Date prédiction')

    class Meta:
        verbose_name = 'Résultat de prédiction'
        verbose_name_plural = 'Résultats de prédiction'
        ordering = ['-date_prediction']

    def __str__(self):
        statut = 'MALADE' if self.est_malade else 'SAIN'
        return f'{self.animal} — {statut} ({self.probabilite:.0%}) — {self.date_prediction:%d/%m/%Y}'
