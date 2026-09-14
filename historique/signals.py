"""
Signals — création automatique d'un HistoriqueEvenement à chaque
enregistrement d'une alimentation, d'un suivi santé ou d'une gestation.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def _create_evenement(ferme, animal, type_evenement, titre, description, source_ia=False):
    """Crée silencieusement un HistoriqueEvenement sans importer en tête de module."""
    from historique.models import HistoriqueEvenement
    HistoriqueEvenement.objects.create(
        ferme          = ferme,
        animal         = animal,
        type_evenement = type_evenement,
        titre          = titre,
        description    = description,
        date_evenement = timezone.now(),
        source_ia      = source_ia,
    )


# ── Alimentation ──────────────────────────────────────────────────────────────
@receiver(post_save, sender='alimentation.Alimentation')
def on_alimentation_saved(sender, instance, created, **kwargs):
    if not created:
        return
    type_nom = instance.type_aliment.nom if instance.type_aliment else '—'
    freq_nom = instance.frequence.nom    if instance.frequence    else ''
    desc     = f'{type_nom}, {instance.quantite_kg} kg'
    if freq_nom:
        desc += f', {freq_nom}'
    _create_evenement(
        ferme          = instance.ferme,
        animal         = instance.animal,
        type_evenement = 'Alimentation',
        titre          = 'Alimentation enregistrée',
        description    = desc,
    )


# ── Suivi santé ───────────────────────────────────────────────────────────────
@receiver(post_save, sender='sante.SuiviSante')
def on_sante_saved(sender, instance, created, **kwargs):
    if not created:
        return
    _create_evenement(
        ferme          = instance.ferme,
        animal         = instance.animal,
        type_evenement = 'Santé',
        titre          = f'Suivi santé — {instance.statut}',
        description    = instance.note or '',
    )


# ── Gestation ─────────────────────────────────────────────────────────────────
@receiver(post_save, sender='gestation.Gestation')
def on_gestation_saved(sender, instance, created, **kwargs):
    if not created:
        return
    _create_evenement(
        ferme          = instance.ferme,
        animal         = instance.animal,
        type_evenement = 'Gestation',
        titre          = 'Gestation enregistrée',
        description    = f'Statut : {instance.statut}. Date prévue : {instance.date_prevue}.',
    )
