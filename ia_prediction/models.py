from django.db import models
from django.conf import settings
from moncheptel.models import Animal


class PredictionResultat(models.Model):
    """Stocke chaque résultat de prédiction IA pour un animal."""

    DECLENCHEUR_CHOICES = [
        ('alimentation', 'Alimentation'),
        ('sante',        'Suivi santé'),
        ('gestation',    'Gestation'),
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


class PreDiagnostic(models.Model):
    """Analyse assistée conservée dans l'historique de santé de l'animal."""
    URGENCE_CHOICES = [('faible', 'Faible'), ('modérée', 'Modérée'), ('élevée', 'Élevée')]
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pre_diagnostics', null=True, blank=True)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='pre_diagnostics', null=True, blank=True)
    historique_evenement = models.ForeignKey('historique.HistoriqueEvenement', on_delete=models.SET_NULL, related_name='pre_diagnostics', null=True, blank=True)
    photo = models.ImageField(upload_to='pre_diagnostics/', blank=True)
    description = models.TextField()
    conversation = models.JSONField(default=list, blank=True)
    espece_image = models.CharField(max_length=20, blank=True)
    suggestions = models.JSONField(default=list)
    recommandations = models.JSONField(default=list)
    urgence = models.CharField(max_length=20, choices=URGENCE_CHOICES, default='modérée')
    limites = models.TextField(blank=True)
    modele = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Pré-diagnostic'
        verbose_name_plural = 'Pré-diagnostics'

    def __str__(self):
        sujet = str(self.animal) if self.animal else 'sans animal associé'
        return f'Pré-diagnostic {sujet} — {self.date_creation:%d/%m/%Y}'
