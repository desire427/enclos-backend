from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Ordonnance, RappelOrdonnance, TraitementOrdonnance
from .reminders import parse_instructions, parse_medication_schedules
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


@receiver(pre_save, sender=Ordonnance)
def on_ordonnance_pre_save(sender, instance, **kwargs):
    previous = sender.objects.filter(pk=instance.pk).values('instructions', 'medicaments').first() if instance.pk else None
    instance._prescription_avant = previous


@receiver(post_save, sender=Ordonnance)
def on_ordonnance_post_save(sender, instance, created, **kwargs):
    previous = getattr(instance, '_prescription_avant', None)
    if not created and previous == {'instructions': instance.instructions, 'medicaments': instance.medicaments}:
        return
    RappelOrdonnance.objects.filter(ordonnance=instance, actif=True).update(actif=False)
    TraitementOrdonnance.objects.filter(ordonnance=instance, actif=True).update(actif=False)
    generic_schedules = [
        RappelOrdonnance(ordonnance=instance, **schedule)
        for schedule in parse_instructions(instance.instructions)
    ]
    RappelOrdonnance.objects.bulk_create(generic_schedules)

    for schedule in parse_medication_schedules(
        instance.medicaments, instance.instructions, instance.date_prescription,
    ):
        treatment = TraitementOrdonnance.objects.create(
            ordonnance=instance,
            medicament=schedule['medicament'],
            posologie=schedule['posologie'],
        )
        RappelOrdonnance.objects.bulk_create([
            RappelOrdonnance(ordonnance=instance, traitement=treatment, **reminder)
            for reminder in schedule['rappels']
        ])
