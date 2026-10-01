from django.db import models
from fermes.models import Ferme
from moncheptel.models import Animal


class SuiviSante(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE, related_name='sante_suivis', verbose_name='Ferme')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='sante_suivis', verbose_name='Animal')
    date_debut = models.DateField(null=True, blank=True, verbose_name='Date début')
    date_prochaine_consultation = models.DateField(null=True, blank=True, verbose_name='Date prochaine consultation')
    date_fin = models.DateField(null=True, blank=True, verbose_name='Date de fin / guérison')
    statut = models.CharField(max_length=80, verbose_name='Statut')
    # Ces mesures viennent directement du formulaire de suivi santé. Elles sont
    # facultatives afin de préserver les suivis déjà créés, mais lorsqu'elles
    # sont renseignées elles alimentent la prédiction IA.
    poids_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Poids actuel (kg)')
    temperature_celsius = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Température (°C)')
    frequence_cardiaque = models.PositiveIntegerField(null=True, blank=True, verbose_name='Fréquence cardiaque (bpm)')
    note = models.TextField(blank=True, verbose_name='Note')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Date de modification')

    class Meta:
        verbose_name = 'Suivi santé'
        verbose_name_plural = 'Suivis santé'

    def __str__(self):
        return f'{self.animal} - {self.statut}'


class Ordonnance(models.Model):
    """Ordonnance vétérinaire rattachée à un animal et à son suivi."""
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE, related_name='ordonnances')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='ordonnances')
    suivi_sante = models.ForeignKey(SuiviSante, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordonnances')
    titre = models.CharField(max_length=150)
    veterinaire = models.CharField(max_length=150, blank=True)
    date_prescription = models.DateField()
    medicaments = models.TextField()
    instructions = models.TextField(blank=True)
    document = models.FileField(upload_to='ordonnances/', null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_prescription', '-id']
        verbose_name = 'Ordonnance'
        verbose_name_plural = 'Ordonnances'

    def __str__(self):
        return f'{self.titre} — {self.animal}'
