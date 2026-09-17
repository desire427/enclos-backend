"""
Moteur de prédiction IA — Random Forest + SHAP + envoi vers n8n.

Flux :
  1. Construire le vecteur de features à partir des données de l'animal
  2. Charger le modèle (cache en mémoire)
  3. Prédire (malade / sain) + probabilité
  4. Calculer les valeurs SHAP
  5. Envoyer le tout au webhook n8n
  6. Persister le résultat en BDD
"""

import json
import logging
import threading
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ── Chemin du modèle (relatif à ce fichier) ──────────────────────────────────
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / 'models' / 'model_soutenance_simplon.joblib'

# ── Cache du modèle (chargé une seule fois) ───────────────────────────────────
_model = None
_model_lock = threading.Lock()


def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                import joblib
                _model = joblib.load(MODEL_PATH)
                logger.info('Modèle IA chargé depuis %s', MODEL_PATH)
    return _model


# ── Liste exacte des 112 features dans l'ordre du modèle ─────────────────────
FEATURES = [
    'age_mois', 'poids_kg', 'temperature_celsius', 'frequence_cardiaque',
    'quantite_aliment_kg', 'frequence_alimentation',
    'espece_caprin', 'espece_ovin', 'espece_porcin',
    'race_Africander', 'race_Alpine', 'race_Angora', 'race_Angus',
    'race_Ankole', 'race_Australian_Friesian_Sahiwal',
    'race_Australian_Milking_Zebu', 'race_Ayrshire', 'race_Belted Galloway',
    'race_Berkshire', 'race_Blackface', 'race_Boer', 'race_Boran',
    'race_Border Leicester', 'race_Brahman', 'race_Brown Swiss',
    'race_Brown_Swiss', 'race_Butana', 'race_Charolais', 'race_Chester White',
    'race_Cheviot', 'race_Corriedale', 'race_Danish_Red', 'race_Deoni',
    'race_Dexter', 'race_Dorper', 'race_Dorset', 'race_Duroc',
    'race_Exotic_Local_Cross', 'race_Finnsheep', 'race_Fleckvieh',
    'race_Gangatiri', 'race_Gir', 'race_Girolando', 'race_Guernsey',
    'race_Hampshire', 'race_Hariana', 'race_Hereford', 'race_Holstein',
    'race_Holstein-Friesian', 'race_Holstein_Zebu_Cross',
    'race_Illawarra_Shorthorn', 'race_Jersey', 'race_Jersey_Zebu_Cross',
    'race_Kankrej', 'race_Karakul', 'race_Kenana', 'race_Kiko',
    'race_Krishna_Valley', 'race_LaMancha', 'race_Landrace',
    'race_Large White', 'race_Leicester Longwool', 'race_Limousin',
    'race_Lincoln', 'race_Merino', 'race_Milking_Shorthorn',
    'race_Montbeliarde', 'race_NDama', 'race_Nigerian Dwarf',
    'race_Normande', 'race_Norwegian_Red', 'race_Nubian', 'race_Ongole',
    'race_Pietrain', 'race_Poland China', 'race_Rambouillet', 'race_Rathi',
    'race_Red Angus', 'race_Red Poll', 'race_Red_Poll_Africa',
    'race_Red_Sindhi', 'race_Romney', 'race_Saanen', 'race_Sahiwal',
    'race_Shorthorn', 'race_Simmental', 'race_Southdown', 'race_Suffolk',
    'race_Tamworth', 'race_Texel', 'race_Tharparkar', 'race_Tipo_Carora',
    'race_Toggenburg', 'race_Tunis', 'race_Wessex Saddleback',
    'race_White_Fulani', 'race_Yorkshire', 'race_Zebu_Cross_Brazil',
    'sexe_male',
    'aliment_type_Crop_Residues', 'aliment_type_Dry_Fodder',
    'aliment_type_Green_Fodder', 'aliment_type_Hay', 'aliment_type_Mixed_Feed',
    'aliment_type_Pasture_Grass', 'aliment_type_Silage',
    'aliment_type_inconnu',
    'gestation_stade_2e trimestre', 'gestation_stade_3e trimestre',
    'gestation_stade_inconnu',
    'source_donnee_Kaggle - Animal Disease Prediction Using Symptoms',
    'source_donnee_Kaggle - Global Cattle Disease Detection + Global Cattle Milk Yield Prediction (fusionnés)',
]


def _age_en_mois(date_naissance):
    """Calcule l'âge en mois depuis la date de naissance."""
    if not date_naissance:
        return 24  # valeur par défaut neutre
    today = date.today()
    if isinstance(date_naissance, str):
        try:
            date_naissance = date.fromisoformat(date_naissance)
        except ValueError:
            return 24
    return max(1, (today.year - date_naissance.year) * 12 +
               (today.month - date_naissance.month))


def _race_feature(race_nom):
    """Retourne le nom de la feature race correspondante ou None."""
    if not race_nom:
        return None
    # Normalise : espaces → underscore pour la plupart, mais certaines gardent les espaces
    key_with_space = f'race_{race_nom}'
    key_underscore = f'race_{race_nom.replace(" ", "_")}'
    if key_with_space in FEATURES:
        return key_with_space
    if key_underscore in FEATURES:
        return key_underscore
    return None


def _aliment_feature(type_aliment_nom):
    """Retourne la feature aliment correspondante."""
    if not type_aliment_nom:
        return 'aliment_type_inconnu'
    mapping = {
        'hay':            'aliment_type_Hay',
        'foin':           'aliment_type_Hay',
        'silage':         'aliment_type_Silage',
        'ensilage':       'aliment_type_Silage',
        'pasture':        'aliment_type_Pasture_Grass',
        'paturage':       'aliment_type_Pasture_Grass',
        'green':          'aliment_type_Green_Fodder',
        'vert':           'aliment_type_Green_Fodder',
        'dry':            'aliment_type_Dry_Fodder',
        'sec':            'aliment_type_Dry_Fodder',
        'mixed':          'aliment_type_Mixed_Feed',
        'melange':        'aliment_type_Mixed_Feed',
        'grain':          'aliment_type_Mixed_Feed',
        'granule':        'aliment_type_Mixed_Feed',
        'crop':           'aliment_type_Crop_Residues',
        'residus':        'aliment_type_Crop_Residues',
    }
    lower = type_aliment_nom.lower()
    for key, feature in mapping.items():
        if key in lower:
            return feature
    return 'aliment_type_inconnu'


def _gestation_stade(animal):
    """Détermine le stade de gestation actif de l'animal."""
    try:
        from gestation.models import Gestation
        gest = Gestation.objects.filter(animal=animal).exclude(
            statut__in=('Terminée', 'terminee', 'terminée')
        ).order_by('-date_debut').first()
        if not gest:
            return None
        jours = (date.today() - gest.date_debut).days if gest.date_debut else 0
        if jours < 90:
            return 'gestation_stade_2e trimestre'   # approximation
        elif jours < 180:
            return 'gestation_stade_3e trimestre'
        else:
            return 'gestation_stade_inconnu'
    except Exception:
        return None


def _derniere_alimentation(animal):
    from alimentation.models import Alimentation
    return Alimentation.objects.filter(animal=animal).select_related(
        'type_aliment', 'frequence'
    ).order_by('-date_alimentation', '-id').first()


def _mesures_sante(animal):
    from sante.models import SuiviSante
    return list(SuiviSante.objects.filter(animal=animal).exclude(
        poids_kg__isnull=True,
        temperature_celsius__isnull=True,
        frequence_cardiaque__isnull=True,
    ).order_by('-date_debut', '-id'))


def _comparaison_historique(mesures):
    """Compare la dernière mesure aux précédentes, sans fabriquer de données."""
    if len(mesures) < 2:
        return {'disponible': False, 'raison': 'Historique insuffisant (au moins deux suivis mesurés requis).'}
    actuelle, historiques = mesures[0], mesures[1:]
    resultat = {'disponible': True, 'mesures': {}}
    for champ in ('poids_kg', 'temperature_celsius', 'frequence_cardiaque'):
        valeur = getattr(actuelle, champ)
        valeurs = [float(getattr(m, champ)) for m in historiques if getattr(m, champ) is not None]
        if valeur is None or not valeurs:
            continue
        moyenne = sum(valeurs) / len(valeurs)
        ecart = float(valeur) - moyenne
        resultat['mesures'][champ] = {
            'actuelle': float(valeur), 'moyenne_historique': round(moyenne, 2),
            'ecart': round(ecart, 2), 'ecart_pct': round((ecart / moyenne) * 100, 2) if moyenne else None,
        }
    return resultat


def build_features(animal, alimentation=None, suivi_sante=None):
    """
    Construit le DataFrame de features pour une prédiction.

    :param animal: instance de moncheptel.models.Animal
    :param alimentation: instance de alimentation.models.Alimentation (optionnel)
    :return: pd.DataFrame avec les 112 colonnes dans l'ordre exact
    """
    # Vecteur de base — tout à 0
    row = {f: 0 for f in FEATURES}

    # ── Features numériques ───────────────────────────────────────────────────
    row['age_mois']             = _age_en_mois(animal.date_naissance)
    # Seules les valeurs saisies sont utilisées. Les valeurs de repli sont
    # nécessaires au modèle, mais restent explicitement signalées à n8n.
    if suivi_sante is None:
        mesures_existantes = _mesures_sante(animal)
        suivi_sante = mesures_existantes[0] if mesures_existantes else None
    row['poids_kg'] = float(suivi_sante.poids_kg) if suivi_sante and suivi_sante.poids_kg is not None else float(animal.poids_naissance or 0)
    row['temperature_celsius'] = float(suivi_sante.temperature_celsius) if suivi_sante and suivi_sante.temperature_celsius is not None else 38.5
    row['frequence_cardiaque'] = float(suivi_sante.frequence_cardiaque) if suivi_sante and suivi_sante.frequence_cardiaque is not None else 70

    alimentation = alimentation or _derniere_alimentation(animal)

    if alimentation:
        row['quantite_aliment_kg']   = float(alimentation.quantite_kg or 0)
        # frequence_alimentation : 1=quotidien, 2=biquotidien, etc.
        freq_nom = (alimentation.frequence.nom if alimentation.frequence else '').lower()
        if 'bi' in freq_nom or '2' in freq_nom:
            row['frequence_alimentation'] = 2
        elif 'tri' in freq_nom or '3' in freq_nom:
            row['frequence_alimentation'] = 3
        elif 'hebdo' in freq_nom:
            row['frequence_alimentation'] = 0.14
        else:
            row['frequence_alimentation'] = 1
    else:
        row['quantite_aliment_kg']   = 0
        row['frequence_alimentation'] = 0

    # ── Espèce (one-hot — bovin est la référence, donc absent) ───────────────
    espece_lower = (animal.espece or '').lower()
    if espece_lower == 'caprin':
        row['espece_caprin'] = 1
    elif espece_lower == 'ovin':
        row['espece_ovin'] = 1
    elif espece_lower == 'porcin':
        row['espece_porcin'] = 1
    # bovin → toutes les features espèce = 0 (référence)

    # ── Race (one-hot) ────────────────────────────────────────────────────────
    race_nom = animal.race.nom if animal.race else ''
    race_feat = _race_feature(race_nom)
    if race_feat:
        row[race_feat] = 1

    # ── Sexe ─────────────────────────────────────────────────────────────────
    if (animal.sexe or '').lower() == 'male':
        row['sexe_male'] = 1

    # ── Type d'aliment ────────────────────────────────────────────────────────
    if alimentation and alimentation.type_aliment:
        aliment_feat = _aliment_feature(alimentation.type_aliment.nom)
        row[aliment_feat] = 1
    else:
        row['aliment_type_inconnu'] = 1

    # ── Gestation ────────────────────────────────────────────────────────────
    stade = _gestation_stade(animal)
    if stade:
        row[stade] = 1

    # ── Source de données (toujours interne) ─────────────────────────────────
    # On n'active aucune source externe — les features restent à 0

    return pd.DataFrame([row], columns=FEATURES)


def predict(animal, alimentation=None, suivi_sante=None, declencheur='manuel'):
    """
    Lance la prédiction complète pour un animal.

    Retourne un dict avec :
      - est_malade (bool)
      - probabilite (float)
      - shap_values (dict feature → valeur)
      - features_used (dict)
    """
    import shap

    model = get_model()
    mesures = _mesures_sante(animal)
    df = build_features(animal, alimentation, suivi_sante)

    # ── Prédiction ────────────────────────────────────────────────────────────
    proba_array = model.predict_proba(df)[0]   # [P(sain), P(malade)]
    est_malade  = bool(proba_array[1] >= 0.5)
    probabilite = float(proba_array[1])

    # ── SHAP ─────────────────────────────────────────────────────────────────
    explainer   = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(df)
    # SHAP varie selon sa version : liste [classe][ligne][feature] ou tableau
    # [ligne][feature][classe]. On extrait toujours la classe « malade ».
    if isinstance(shap_vals, list):
        shap_class1 = shap_vals[1][0]
    elif np.asarray(shap_vals).ndim == 3:
        shap_class1 = shap_vals[0, :, 1]
    else:
        shap_class1 = shap_vals[0]
    shap_dict   = {
        feat: round(float(val), 6)
        for feat, val in zip(FEATURES, shap_class1)
        if abs(val) > 1e-7   # ne garder que les contributions non nulles
    }

    return {
        'est_malade':  est_malade,
        'probabilite': probabilite,
        'shap_values': shap_dict,
        'features_used': df.iloc[0].to_dict(),
        'comparaison_historique': _comparaison_historique(mesures),
    }


def _est_vrai(valeur):
    if valeur is True:
        return True
    if isinstance(valeur, str):
        return valeur.strip().lower() in {'1', 'true', 'oui', 'yes', 'vrai'}
    if isinstance(valeur, (int, float)):
        return valeur != 0
    return False


def _normaliser_reponse_n8n(data):
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return {}
    for key in ('json', 'body', 'data'):
        inner = data.get(key)
        if isinstance(inner, list) and inner:
            inner = inner[0]
        if isinstance(inner, dict) and any(
            champ in inner for champ in ('creer_alerte', 'explication_llm', 'message_alerte')
        ):
            return inner
    return data


def _variation_poids(animal):
    avant = getattr(animal, '_poids_avant', None)
    apres = animal.poids_naissance
    if avant is None or apres is None:
        return None
    avant_f, apres_f = float(avant), float(apres)
    if round(avant_f, 2) == round(apres_f, 2):
        return None
    return avant_f, apres_f


def _creer_alerte(animal, niveau, message):
    from alertes.models import Alerte

    if not message:
        return None
    if Alerte.objects.filter(
        ferme=animal.ferme, animal=animal, message=message, statut='non_lue',
    ).exists():
        return None
    return Alerte.objects.create(
        ferme=animal.ferme, animal=animal,
        type_alerte=niveau, message=message,
    )


def _alerte_depuis_n8n(animal, reponse_n8n):
    message = str(reponse_n8n.get('message_alerte') or reponse_n8n.get('alerte_message') or '').strip()
    if not _est_vrai(reponse_n8n.get('creer_alerte')) or not message:
        return None
    niveau = str(reponse_n8n.get('niveau_alerte') or 'Avertissement')
    return _creer_alerte(animal, niveau, message)


def _alerte_variation_poids(animal):
    """Alerte si le poids vient d'être modifié directement sur la fiche animal."""
    variation = _variation_poids(animal)
    if not variation:
        return None
    avant_f, apres_f = variation
    delta = abs(apres_f - avant_f)
    delta_pct = (delta / avant_f * 100) if avant_f else 100
    if delta < 2 and delta_pct < 10:
        return None
    nom = animal.nom or animal.numero_identification
    niveau = 'Avertissement' if delta_pct >= 20 or delta >= 5 else 'Info'
    message = f'Le poids de {nom} est passé de {avant_f:.2f} kg à {apres_f:.2f} kg.'
    return _creer_alerte(animal, niveau, message)


def _alerte_perte_poids_suivi(animal):
    """
    Détecte une perte de poids dans l'historique SuiviSante indépendamment
    d'une modification de la fiche animal.
    Déclenche une alerte si la dernière mesure est inférieure à la moyenne
    des mesures précédentes d'au moins 5 % ou 2 kg.
    """
    mesures = _mesures_sante(animal)
    if len(mesures) < 2:
        return None
    derniere = mesures[0]
    if derniere.poids_kg is None:
        return None
    poids_precedents = [
        float(m.poids_kg) for m in mesures[1:] if m.poids_kg is not None
    ]
    if not poids_precedents:
        return None
    moyenne_avant = sum(poids_precedents) / len(poids_precedents)
    poids_actuel = float(derniere.poids_kg)
    delta = moyenne_avant - poids_actuel  # positif = perte
    if delta <= 0:
        return None  # pas de perte
    delta_pct = (delta / moyenne_avant * 100) if moyenne_avant else 100
    if delta < 2 and delta_pct < 5:
        return None
    nom = animal.nom or animal.numero_identification
    niveau = 'Avertissement' if delta_pct >= 10 or delta >= 5 else 'Info'
    message = f'{nom} a perdu du poids récemment, surveillez son état.'
    return _creer_alerte(animal, niveau, message)


# Mots-clés indiquant un comportement ou état préoccupant dans les observations
_MOTS_CLES_ALERTE = [
    'moins réactif', 'pas réactif', 'peu réactif',
    'apathi', 'apathique',
    'faible', 'très faible',
    'abattu', 'prostré', 'prostration',
    'ne mange pas', 'refuse de manger', 'perte d\'appétit', 'manque d\'appétit',
    'diarrhée', 'diarrhee',
    'fièvre', 'fievre',
    'boite', 'boiterie', 'boiteux',
    'toux', 'respiration difficile', 'essoufflé',
    'tremble', 'tremblements',
    'ne se lève pas', 'ne se leve pas', 'couché', 'couche',
    'déshydrat', 'deshydrat',
    'abcès', 'abces', 'blessure', 'plaie',
]


def _alerte_comportement(animal, suivi_sante=None):
    """
    Crée une alerte locale si les observations de l'animal OU la note du
    suivi santé contiennent des signaux préoccupants, sans attendre n8n.
    """
    observations = (animal.observations or '').lower().strip()
    note_suivi   = (getattr(suivi_sante, 'note', None) or '').lower().strip()
    texte        = ' '.join(filter(None, [observations, note_suivi]))
    if not texte:
        return None
    for mot in _MOTS_CLES_ALERTE:
        if mot in texte:
            nom    = animal.nom or animal.numero_identification
            source = animal.observations if mot in observations else suivi_sante.note
            message = (
                f'{nom} présente un signe préoccupant : "{mot}". '
                f'Note : {source}'
            )
            return _creer_alerte(animal, 'Avertissement', message)
    return None



def _historiser_prediction(animal, pr, explication):
    from django.utils import timezone
    from historique.models import HistoriqueEvenement

    titre = 'Analyse IA'
    HistoriqueEvenement.objects.create(
        ferme=animal.ferme,
        animal=animal,
        type_evenement='IA',
        titre=titre,
        description=explication or f'Probabilité estimée : {pr.probabilite:.0%}.',
        date_evenement=timezone.now(),
        source_ia=True,
    )


def envoyer_n8n(animal, resultat, n8n_url, declencheur='manuel', gestation=None):
    """
    Envoie le résultat + SHAP au webhook n8n pour justification LLM.
    Retourne True si succès, False sinon.
    """
    shap_lines = '\n'.join(
        f'{feature}: {value:+.6f}'
        for feature, value in sorted(
            resultat['shap_values'].items(), key=lambda item: abs(item[1]), reverse=True
        )[:12]
    )
    comparaison = resultat['comparaison_historique']
    historique_lines = json.dumps(comparaison, ensure_ascii=False)

    suivi_sante = resultat.get('suivi_sante')
    observations_parts = [
        f"État de santé déclaré dans le formulaire : {animal.get_etat_sante_display()}",
        animal.observations or '',
    ]
    if suivi_sante:
        observations_parts.append(f"Suivi santé : {suivi_sante['statut']}")
        if suivi_sante['note']:
            observations_parts.append(suivi_sante['note'])
    if gestation and gestation.note:
        observations_parts.append(f"Gestation : {gestation.note}")

    poids_kg = resultat['features_used'].get('poids_kg')
    variation = _variation_poids(animal)
    payload = {
        # Champs plats : utilisés par le workflow n8n « Préparer les données ».
        'animal_id': animal.id,
        'nom': animal.nom or animal.numero_identification,
        'espece': animal.espece or '',
        'etat_sante': animal.etat_sante or '',
        'presence': animal.presence or '',
        'poids_kg': poids_kg,
        'poids_precedent': variation[0] if variation else None,
        'proba': resultat['probabilite'],
        'prediction_label': 'malade' if resultat['est_malade'] else 'sain',
        'observations': '\n'.join(filter(None, observations_parts)),
        'shap_lines': shap_lines,
        'historique_lines': historique_lines,
        # Données structurées : utiles pour faire évoluer le workflow sans
        # perdre d'information.
        'animal': {
            'id': animal.id,
            'numero_identification': animal.numero_identification,
            'nom': animal.nom or '',
            'espece': animal.espece or '',
            'race': animal.race.nom if animal.race else '',
            'sexe': animal.sexe or '',
            'etat_sante': animal.etat_sante or '',
            'presence': animal.presence or '',
            'poids_kg': poids_kg,
            'age_mois': _age_en_mois(animal.date_naissance),
        },
        'prediction': {
            'est_malade':  resultat['est_malade'],
            'probabilite': resultat['probabilite'],
            'declencheur': declencheur,
        },
        'gestation': ({
            'id': gestation.id,
            'statut': gestation.statut,
            'date_saillie': gestation.date_debut.isoformat() if gestation.date_debut else None,
            'date_prevue': gestation.date_prevue.isoformat() if gestation.date_prevue else None,
            'date_mise_bas_reelle': gestation.date_mise_bas_reelle.isoformat() if gestation.date_mise_bas_reelle else None,
            'nombre_naissances': gestation.nombre_naissances,
            'note': gestation.note,
        } if gestation else None),
        'suivi_sante': suivi_sante,
        'shap_values':   resultat['shap_values'],
        'features_used': {
            k: v for k, v in resultat['features_used'].items()
            if v != 0  # envoyer uniquement les features actives
        },
        'comparaison_historique': resultat['comparaison_historique'],
    }
    try:
        resp = requests.post(
            n8n_url,
            json=payload,
            timeout=15,
            headers={'Content-Type': 'application/json'},
        )
        resp.raise_for_status()
        logger.info('Résultat IA envoyé à n8n pour animal %s (status %s)', animal.id, resp.status_code)
        try:
            data = resp.json()
        except ValueError:
            data = {}
        return True, _normaliser_reponse_n8n(data)
    except requests.RequestException as exc:
        logger.warning('Échec envoi n8n pour animal %s : %s', animal.id, exc)
        return False, {}


def run_prediction(animal, alimentation=None, suivi_sante=None, gestation=None, declencheur='manuel'):
    """
    Fonction principale — prédit, envoie à n8n, persiste le résultat.
    Appelée depuis les signals ou l'API.
    Retourne l'instance PredictionResultat créée.
    """
    from django.conf import settings
    from ia_prediction.models import PredictionResultat

    n8n_url = getattr(settings, 'N8N_WEBHOOK_URL', '')

    try:
        resultat = predict(animal, alimentation, suivi_sante, declencheur)
        if suivi_sante:
            resultat['suivi_sante'] = {
                'id': suivi_sante.id,
                'statut': suivi_sante.statut,
                'note': suivi_sante.note or '',
                'date_debut': suivi_sante.date_debut.isoformat() if suivi_sante.date_debut else None,
                'date_prochaine_consultation': (
                    suivi_sante.date_prochaine_consultation.isoformat()
                    if suivi_sante.date_prochaine_consultation else None
                ),
                'poids_kg': float(suivi_sante.poids_kg) if suivi_sante.poids_kg is not None else None,
                'temperature_celsius': float(suivi_sante.temperature_celsius) if suivi_sante.temperature_celsius is not None else None,
                'frequence_cardiaque': suivi_sante.frequence_cardiaque,
            }
    except Exception as exc:
        logger.error('Erreur prédiction IA pour animal %s : %s', animal.id, exc, exc_info=True)
        return None

    # Envoyer à n8n si l'URL est configurée
    envoye = False
    reponse_n8n = {}
    if n8n_url:
        envoye, reponse_n8n = envoyer_n8n(animal, resultat, n8n_url, declencheur, gestation)

    # Le texte destiné à l'éleveur vient exclusivement de n8n / du LLM.
    explication = str(
        reponse_n8n.get('explication_llm')
        or reponse_n8n.get('explication')
        or reponse_n8n.get('conseil')
        or ''
    )

    # Persister en base
    pr = PredictionResultat.objects.create(
        animal = animal,
        declencheur = declencheur,
        est_malade = resultat['est_malade'],
        probabilite = resultat['probabilite'],
        shap_values = resultat['shap_values'],
        features_used = {k: v for k, v in resultat['features_used'].items() if v != 0},
        comparaison_historique = resultat['comparaison_historique'],
        envoye_n8n = envoye,
        explication_llm = explication,
    )

    # ── Alertes sanitaires ───────────────────────────────────────────────────
    # 1. Alerte demandée par n8n / LLM (prioritaire)
    _alerte_depuis_n8n(animal, reponse_n8n)

    # 2. Variation de poids sur la fiche animal (modification directe)
    _alerte_variation_poids(animal)

    # 3. Perte de poids détectée dans l'historique SuiviSante
    _alerte_perte_poids_suivi(animal)

    # 4. Observations comportementales suspectes (sans attendre n8n)
    _alerte_comportement(animal, suivi_sante)

    _historiser_prediction(animal, pr, explication)

    logger.info(
        'Prédiction animal %s : %s (%.0f%%) — décl. %s',
        animal.id,
        'MALADE' if pr.est_malade else 'SAIN',
        pr.probabilite * 100,
        declencheur,
    )
    return pr
