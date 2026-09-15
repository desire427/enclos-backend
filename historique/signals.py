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


# ── Animal ajouté ou modifié ──────────────────────────────────────────────────
@receiver(post_save, sender='moncheptel.Animal')
def on_animal_saved(sender, instance, created, **kwargs):
    if created:
        titre = 'Animal ajouté'
        desc  = f'{instance.nom or instance.numero_identification} a été enregistré dans le cheptel.'
    else:
        titre = 'Animal modifié'
        desc  = instance.observations or ''
    _create_evenement(
        ferme          = instance.ferme,
        animal         = instance,
        type_evenement = 'Animal',
        titre          = titre,
        description    = desc,
    )


# ── Alimentation ──────────────────────────────────────────────────────────────
@receiver(post_save, sender='alimentation.Alimentation')
def on_alimentation_saved(sender, instance, created, **kwargs):
    type_nom = instance.type_aliment.nom if instance.type_aliment else '—'
    freq_nom = instance.frequence.nom    if instance.frequence    else ''
    desc     = f'{type_nom}, {instance.quantite_kg} kg'
    if freq_nom:
        desc += f', {freq_nom}'
    titre = 'Alimentation enregistrée' if created else 'Alimentation modifiée'
    _create_evenement(
        ferme          = instance.ferme,
        animal         = instance.animal,
        type_evenement = 'Alimentation',
        titre          = titre,
        description    = desc,
    )


# ── Suivi santé ───────────────────────────────────────────────────────────────
@receiver(post_save, sender='sante.SuiviSante')
def on_sante_saved(sender, instance, created, **kwargs):
    # Éviter le doublon quand sync.py historise lui-même via _historiser()
    if getattr(instance, '_skip_animal_sync', False) and not created:
        return
    statut_avant = getattr(instance, '_statut_avant', None)
    # Pour une modification : n'historiser que si le statut a réellement changé
    if not created and statut_avant is not None and statut_avant == instance.statut:
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
