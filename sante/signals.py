from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .sync import aligner_dates_suivi, synchroniser_animal_depuis_suivi, synchroniser_suivis_depuis_animal


@receiver(pre_save, sender='sante.SuiviSante')
def on_suivi_pre_save(sender, instance, **kwargs):
    if instance.pk:
        instance._statut_avant = sender.objects.filter(pk=instance.pk).values_list('statut', flat=True).first()
    else:
        instance._statut_avant = None
    aligner_dates_suivi(instance)


@receiver(post_save, sender='sante.SuiviSante')
def on_suivi_post_save(sender, instance, **kwargs):
    synchroniser_animal_depuis_suivi(instance)


@receiver(post_save, sender='moncheptel.Animal')
def on_animal_post_save(sender, instance, created, **kwargs):
    if created:
        return
    synchroniser_suivis_depuis_animal(instance)
