from datetime import date

from django.utils import timezone

ETAT_VERS_STATUT = {
    'malade': 'Malade',
    'en_traitement': 'En traitement',
}

STATUT_VERS_ETAT = {
    'malade': 'malade',
    'en traitement': 'en_traitement',
    'sous surveillance': 'malade',
    'guéri': 'sain',
    'gueri': 'sain',
}

STATUTS_TERMINES = {'guéri', 'gueri'}


def normaliser_statut(valeur):
    return (valeur or '').strip().lower()


def est_suivi_ouvert(suivi):
    if suivi.date_fin:
        return False
    return normaliser_statut(suivi.statut) not in STATUTS_TERMINES


def etat_depuis_statut(statut):
    return STATUT_VERS_ETAT.get(normaliser_statut(statut))


def _historiser(ferme, animal, titre, description):
    from historique.models import HistoriqueEvenement
    HistoriqueEvenement.objects.create(
        ferme=ferme,
        animal=animal,
        type_evenement='Santé',
        titre=titre,
        description=description or '',
        date_evenement=timezone.now(),
        source_ia=False,
    )


def aligner_dates_suivi(suivi):
    """Ferme ou rouvre le suivi selon son statut, sans toucher à l'animal."""
    if normaliser_statut(suivi.statut) in STATUTS_TERMINES:
        if not suivi.date_fin:
            suivi.date_fin = date.today()
        return
    if suivi.date_fin:
        suivi.date_fin = None


def synchroniser_suivis_depuis_animal(animal):
    """Quand la fiche animal change, le suivi santé ouvert suit le même état."""
    from sante.models import SuiviSante

    if getattr(animal, '_skip_sante_sync', False):
        return
    if animal.etat_sante == 'gestation':
        return

    suivis = list(SuiviSante.objects.filter(animal=animal).order_by('-date_modification', '-id'))
    ouverts = [s for s in suivis if est_suivi_ouvert(s)]

    if animal.etat_sante == 'sain':
        for suivi in ouverts:
            ancien = suivi.statut
            suivi.statut = 'Guéri'
            suivi.date_fin = date.today()
            if animal.observations:
                suivi.note = animal.observations
            suivi._skip_animal_sync = True
            suivi.save()
            if normaliser_statut(ancien) not in STATUTS_TERMINES:
                _historiser(
                    suivi.ferme, animal,
                    'Suivi santé — Guéri',
                    animal.observations or suivi.note,
                )
        return

    statut_cible = ETAT_VERS_STATUT.get(animal.etat_sante)
    if not statut_cible:
        return
    if not ouverts:
        return

    suivi = ouverts[0]
    if suivi.statut == statut_cible and not suivi.date_fin:
        if animal.observations and suivi.note != animal.observations:
            suivi.note = animal.observations
            suivi._skip_animal_sync = True
            suivi.save()
        return
    suivi.statut = statut_cible
    suivi.date_fin = None
    if animal.observations:
        suivi.note = animal.observations
    suivi._skip_animal_sync = True
    suivi.save()


def _appliquer_etat_animal(animal, nouvel_etat, note=''):
    if not animal or not nouvel_etat:
        return
    if nouvel_etat == 'sain' and animal.etat_sante == 'gestation':
        return
    if animal.etat_sante == nouvel_etat:
        return

    animal.etat_sante = nouvel_etat
    animal._skip_sante_sync = True
    if note:
        animal.observations = note
        animal.save(update_fields=['etat_sante', 'observations', 'date_modification'])
        return
    animal.save(update_fields=['etat_sante', 'date_modification'])


def synchroniser_animal_depuis_suivi(suivi):
    """Quand un suivi santé change, l'état de santé de l'animal suit."""
    if getattr(suivi, '_skip_animal_sync', False):
        return
    _appliquer_etat_animal(suivi.animal, etat_depuis_statut(suivi.statut), suivi.note)


def realigner_animaux_depuis_suivis_ouverts():
    """Rattrape les fiches animal restées 'sain' alors qu'un suivi est encore ouvert."""
    from sante.models import SuiviSante

    suivis = list(
        SuiviSante.objects.select_related('animal').order_by('-date_modification', '-id')
    )
    deja_alignes = set()
    for suivi in suivis:
        if suivi.animal_id in deja_alignes:
            continue
        if not est_suivi_ouvert(suivi):
            continue
        deja_alignes.add(suivi.animal_id)
        _appliquer_etat_animal(suivi.animal, etat_depuis_statut(suivi.statut), suivi.note)
