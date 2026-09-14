from django.db import models
from fermes.models import Ferme


# ---------------------------------------------------------------------------
# Choix d'espèces — préfixes utilisés pour la génération du numéro d'ID
# ---------------------------------------------------------------------------
ESPECE_CHOICES = [
    ('bovin',   'Bovin'),
    ('ovin',    'Ovin'),
    ('caprin',  'Caprin'),
    ('porcin',  'Porcin'),
]

ESPECE_PREFIX = {
    'bovin':  'B',
    'ovin':   'O',
    'caprin': 'C',
    'porcin': 'P',
}


# ---------------------------------------------------------------------------
# Races — liées à une espèce, créées par le propriétaire
# ---------------------------------------------------------------------------
class Race(models.Model):
    espece = models.CharField(
        max_length=20,
        choices=ESPECE_CHOICES,
        verbose_name='Espèce',
    )
    nom = models.CharField(max_length=120, verbose_name='Nom de la race')
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        verbose_name = 'Race'
        verbose_name_plural = 'Races'
        unique_together = ('espece', 'nom')
        ordering = ('espece', 'nom')

    def __str__(self):
        return f'{self.get_espece_display()} — {self.nom}'


# ---------------------------------------------------------------------------
# Animal
# ---------------------------------------------------------------------------
class Animal(models.Model):
    SEXE_CHOICES = [
        ('male',    'Mâle'),
        ('femelle', 'Femelle'),
    ]

    # Présence physique de l'animal dans la ferme
    PRESENCE_CHOICES = [
        ('present', 'Présent'),
        ('vendu',   'Vendu'),
        ('mort',    'Mort'),
    ]

    # État de santé de l'animal
    ETAT_SANTE_CHOICES = [
        ('sain',           'Sain'),
        ('malade',         'Malade'),
        ('gestation',      'Gestation'),
        ('en_traitement',  'En traitement'),
    ]

    ferme = models.ForeignKey(
        Ferme,
        on_delete=models.CASCADE,
        related_name='animaux',
        verbose_name='Ferme',
    )
    # Nom facultatif
    nom = models.CharField(max_length=120, blank=True, verbose_name='Nom')

    # Généré automatiquement — ne pas fournir à la création
    numero_identification = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name='Numéro d\'identification',
    )

    espece = models.CharField(
        max_length=20,
        choices=ESPECE_CHOICES,
        verbose_name='Espèce',
    )
    race = models.ForeignKey(
        Race,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='animaux',
        verbose_name='Race',
    )

    sexe = models.CharField(
        max_length=20,
        choices=SEXE_CHOICES,
        default='femelle',
        verbose_name='Sexe',
    )
    date_naissance  = models.DateField(null=True, blank=True, verbose_name='Date de naissance')
    date_arrivee    = models.DateField(null=True, blank=True, verbose_name='Date d\'arrivée')
    date_depart     = models.DateField(null=True, blank=True, verbose_name='Date de départ')
    poids_naissance = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='Poids naissance (kg)',
    )

    # Présence physique (remplace l'ancien statut)
    presence = models.CharField(
        max_length=20,
        choices=PRESENCE_CHOICES,
        default='present',
        verbose_name='Présence',
    )

    # État de santé (séparé de la présence)
    etat_sante = models.CharField(
        max_length=20,
        choices=ETAT_SANTE_CHOICES,
        default='sain',
        verbose_name='État de santé',
    )

    couleur      = models.CharField(max_length=80, blank=True, verbose_name='Couleur')
    observations = models.TextField(blank=True, verbose_name='Observations')

    date_creation      = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification  = models.DateTimeField(auto_now=True,     verbose_name='Date de modification')

    class Meta:
        verbose_name = 'Animal'
        verbose_name_plural = 'Animaux'
        ordering = ['numero_identification']

    def __str__(self):
        return self.nom or self.numero_identification

    # -----------------------------------------------------------------------
    # Génération automatique du numéro d'identification
    # -----------------------------------------------------------------------
    def _generate_numero(self):
        prefix = ESPECE_PREFIX.get(self.espece, 'X')
        count  = Animal.objects.filter(espece=self.espece).count()
        sequence = count + 1
        return f'{prefix}-{sequence:03d}'

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero_identification:
            numero = self._generate_numero()
            while Animal.objects.filter(numero_identification=numero).exists():
                numero_int = int(numero.split('-')[1]) + 1
                prefix = ESPECE_PREFIX.get(self.espece, 'X')
                numero = f'{prefix}-{numero_int:03d}'
            self.numero_identification = numero
        super().save(*args, **kwargs)
