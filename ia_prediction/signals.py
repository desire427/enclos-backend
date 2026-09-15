"""
Signals — déclenche automatiquement la prédiction IA après :
  - création d'une alimentation (indique une mise à jour de l'état nutritionnel)
  - création d'un suivi santé (indique un problème signalé)

La prédiction tourne dans un thread séparé pour ne pas ralentir la requête.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _run_async(animal, alimentation=None, suivi_sante=None, gestation=None, declencheur='alimentation'):
    """Exécute l'analyse après validation effective de l'enregistrement."""
    def task():
        try:
            from ia_prediction.predictor import run_prediction
            run_prediction(
                animal, alimentation=alimentation, suivi_sante=suivi_sante,
                gestation=gestation, declencheur=declencheur,
            )
        except Exception as exc:
            logger.error('Signal IA — erreur prédiction animal %s : %s', animal.id, exc, exc_info=True)

    # L'appel est volontairement synchrone : l'interface ne doit pas annoncer
    # une analyse terminée alors que le thread IA a échoué silencieusement.
    transaction.on_commit(task)


# ── Alimentation créée ────────────────────────────────────────────────────────
@receiver(post_save, sender='alimentation.Alimentation')
def on_alimentation_created(sender, instance, created, **kwargs):
    _run_async(instance.animal, alimentation=instance, declencheur='alimentation')


# ── Suivi santé créé ──────────────────────────────────────────────────────────
@receiver(post_save, sender='sante.SuiviSante')
def on_sante_created(sender, instance, created, **kwargs):
    _run_async(instance.animal, suivi_sante=instance, declencheur='sante')


# ── Fiche animal modifiée ───────────────────────────────────────────────────
@receiver(pre_save, sender='moncheptel.Animal')
def on_animal_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return
    ancien = sender.objects.filter(pk=instance.pk).values_list('poids_naissance', flat=True).first()
    instance._poids_avant = ancien


@receiver(post_save, sender='moncheptel.Animal')
def on_animal_updated(sender, instance, created, **kwargs):
    """Analyse les nouvelles informations saisies dans Modifier un animal."""
    if created:
        return
    _run_async(instance, declencheur='manuel')


# ── Gestation créée ou modifiée ──────────────────────────────────────────────
@receiver(post_save, sender='gestation.Gestation')
def on_gestation_saved(sender, instance, **kwargs):
    _run_async(instance.animal, gestation=instance, declencheur='gestation')
