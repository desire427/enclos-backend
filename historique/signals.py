"""
Signals — création automatique d'un HistoriqueEvenement à chaque
enregistrement d'une alimentation, d'un suivi santé ou d'une gestation.
"""
from django.db.models.signals import post_save, pre_save
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
@receiver(pre_save, sender='moncheptel.Animal')
def capture_animal_state(sender, instance, **kwargs):
    instance._previous_state = sender.objects.filter(pk=instance.pk).values('presence', 'etat_sante').first() if instance.pk else None


@receiver(post_save, sender='moncheptel.Animal')
def on_animal_saved(sender, instance, created, **kwargs):
    if created:
        titre = 'Animal ajouté'
        desc  = f'{instance.nom or instance.numero_identification} a été enregistré dans le cheptel.'
    else:
        previous = getattr(instance, '_previous_state', None) or {}
        state_changed = previous.get('presence') != instance.presence or previous.get('etat_sante') != instance.etat_sante
        titre = 'État de l’animal modifié' if state_changed else 'Animal modifié'
        desc = instance.observations or ''
        if state_changed:
            desc = f"Présence : {previous.get('presence', '—')} → {instance.presence}. Santé : {previous.get('etat_sante', '—')} → {instance.etat_sante}. {desc}".strip()
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
@receiver(pre_save, sender='sante.SuiviSante')
def capture_suivi_state(sender, instance, **kwargs):
    instance._previous_followup = sender.objects.filter(pk=instance.pk).values('statut', 'date_prochaine_consultation', 'note').first() if instance.pk else None


@receiver(post_save, sender='sante.SuiviSante')
def on_sante_saved(sender, instance, created, **kwargs):
    # Éviter le doublon quand sync.py historise lui-même via _historiser()
    if getattr(instance, '_skip_animal_sync', False) and not created:
        return
    previous = getattr(instance, '_previous_followup', None) or {}
    appointment_changed = previous.get('date_prochaine_consultation') != instance.date_prochaine_consultation
    if not created and previous.get('statut') == instance.statut and previous.get('note') == instance.note and not appointment_changed:
        return
    event_type = 'Consultation' if appointment_changed else 'Santé'
    details = instance.note or ''
    if appointment_changed and instance.date_prochaine_consultation:
        details = f"Prochaine consultation : {instance.date_prochaine_consultation}. {details}".strip()
    _create_evenement(
        ferme=instance.ferme, animal=instance.animal, type_evenement=event_type,
        titre=f'Suivi santé — {instance.statut}', description=details,
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


@receiver(post_save, sender='sante.Ordonnance')
def on_ordonnance_saved(sender, instance, created, **kwargs):
    _create_evenement(
        ferme=instance.ferme, animal=instance.animal, type_evenement='Ordonnance',
        titre=('Ordonnance créée — ' if created else 'Ordonnance modifiée — ') + instance.titre,
        description=f"Vétérinaire : {instance.veterinaire or 'Non précisé'}. {instance.medicaments}",
    )
