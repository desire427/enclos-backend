"""
API de prédiction IA.

Endpoints :
  POST /api/ia/predire/          — déclenche une prédiction pour un animal donné
  GET  /api/ia/predictions/      — liste toutes les prédictions de la ferme
  GET  /api/ia/predictions/{id}/ — détail d'une prédiction
  GET  /api/ia/predictions/?animal={id} — prédictions d'un animal
"""

import threading
import base64
import json
import requests

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from moncheptel.models import Animal
from .models import PredictionResultat
from .predictor import run_prediction
from .serializers import PredictionResultatSerializer


class PredictionResultatViewSet(ReadOnlyModelViewSet):
    """Liste / détail des prédictions pour la ferme connectée."""
    serializer_class   = PredictionResultatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = PredictionResultat.objects.select_related('animal').filter(
            animal__ferme__proprietaire=self.request.user
        )
        animal_id = self.request.query_params.get('animal')
        if animal_id:
            qs = qs.filter(animal_id=animal_id)
        return qs


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def predire(request):
    """
    Déclenche une prédiction IA pour un animal.

    Corps JSON attendu :
      {
        "animal_id":      <int>,          // obligatoire
        "alimentation_id": <int|null>,    // optionnel
        "declencheur":    "manuel"        // optionnel
      }
    """
    animal_id       = request.data.get('animal_id')
    alimentation_id = request.data.get('alimentation_id')
    declencheur     = request.data.get('declencheur', 'manuel')

    if not animal_id:
        return Response({'detail': 'animal_id est obligatoire.'}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifier que l'animal appartient à la ferme de l'utilisateur
    try:
        animal = Animal.objects.get(id=animal_id, ferme__proprietaire=request.user)
    except Animal.DoesNotExist:
        return Response({'detail': 'Animal introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    alimentation = None
    if alimentation_id:
        try:
            from alimentation.models import Alimentation
            alimentation = Alimentation.objects.get(id=alimentation_id, animal=animal)
        except Exception:
            pass  # alimentation optionnelle

    # Lancer la prédiction dans un thread pour ne pas bloquer la réponse HTTP
    result_container = {}

    def run():
        pr = run_prediction(animal, alimentation, declencheur)
        result_container['pr'] = pr

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=30)   # attendre max 30s

    pr = result_container.get('pr')
    if not pr:
        return Response(
            {'detail': 'La prédiction a échoué ou a dépassé le délai.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(PredictionResultatSerializer(pr).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def pre_diagnostic(request):
    """Analyse photo et description; enregistre le résultat dans la fiche santé."""
    from django.conf import settings
    from django.utils import timezone
    from historique.models import HistoriqueEvenement
    from .models import PreDiagnostic

    image = request.FILES.get('photo')
    description = (request.data.get('description') or '').strip()
    animal_id = request.data.get('animal_id')
    if not image:
        return Response({'detail': 'Une photo est obligatoire.'}, status=status.HTTP_400_BAD_REQUEST)
    if image.size > 8 * 1024 * 1024:
        return Response({'detail': 'La photo ne peut pas dépasser 8 Mo.'}, status=status.HTTP_400_BAD_REQUEST)
    if image.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        return Response({'detail': 'Formats acceptés : JPEG, PNG ou WebP.'}, status=status.HTTP_400_BAD_REQUEST)
    if len(description) < 5 or len(description) > 3000:
        return Response({'detail': 'La description doit contenir entre 5 et 3 000 caractères.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        animal = Animal.objects.select_related('race').get(id=animal_id, ferme__proprietaire=request.user)
    except (Animal.DoesNotExist, TypeError, ValueError):
        return Response({'detail': 'Animal introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    if animal.presence != 'present':
        return Response({'detail': 'Un pré-diagnostic ne peut pas être demandé pour un animal vendu ou mort.'}, status=status.HTTP_400_BAD_REQUEST)
    if not settings.OPENROUTER_API_KEY:
        return Response({'detail': 'Le service IA n’est pas configuré : ajoutez OPENROUTER_API_KEY au fichier .env.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        from PIL import Image
        checked_image = Image.open(image)
        checked_image.verify()
        image.seek(0)
    except Exception:
        return Response({'detail': 'Le fichier fourni ne contient pas une image valide.'}, status=status.HTTP_400_BAD_REQUEST)
    encoded_image = base64.b64encode(image.read()).decode('ascii')
    context = (f"Espèce : {animal.get_espece_display()}. Race : {animal.race.nom if animal.race else 'non précisée'}. "
               f"Sexe : {animal.get_sexe_display()}. État actuel : {animal.get_etat_sante_display()}.")
    prompt = (
        "Tu es un assistant de pré-diagnostic vétérinaire pour éleveurs. Analyse la photo et les signes rapportés. "
        "Ne donne jamais un diagnostic certain ni médicament ou posologie. Signale les limites de l'image et les signes qui nécessitent un vétérinaire. "
        "Réponds uniquement avec un objet JSON contenant : suggestions (liste d'objets avec nom, justification, niveau), "
        "recommandations (liste d'actions immédiates sûres), urgence (faible, modérée ou élevée), limites (texte). "
        f"\nAnimal : {context}\nDescription orale retranscrite : {description}"
    )
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions', timeout=(10, 60),
            headers={
                'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://enclos.app',
                'X-Title': 'Enclos - Pré-diagnostic animal',
            },
            json={
                'model': settings.OPENROUTER_VISION_MODEL,
                'temperature': 0.2,
                'response_format': {'type': 'json_object'},
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': f'data:{image.content_type};base64,{encoded_image}'}},
                    ],
                }],
            },
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError('La réponse IA doit être un objet JSON.')
        suggestions = result.get('suggestions', [])
        recommendations = result.get('recommandations', [])
        urgency = result.get('urgence', 'modérée')
        if not isinstance(suggestions, list) or not isinstance(recommendations, list):
            raise ValueError('Format de réponse IA invalide.')
        if urgency not in ('faible', 'modérée', 'élevée'):
            urgency = 'modérée'
        limitations = str(result.get('limites') or 'Cette aide au pré-diagnostic ne remplace pas l’examen d’un vétérinaire.')
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return Response({'detail': 'Le pré-diagnostic est momentanément indisponible. Réessayez dans quelques instants.'}, status=status.HTTP_502_BAD_GATEWAY)

    diagnostic = PreDiagnostic.objects.create(
        animal=animal, photo=image, description=description, suggestions=suggestions,
        recommandations=recommendations, urgence=urgency, limites=limitations,
        modele=settings.OPENROUTER_VISION_MODEL,
    )
    HistoriqueEvenement.objects.create(
        ferme=animal.ferme, animal=animal, type_evenement='Pré-diagnostic IA',
        titre='Pré-diagnostic assisté par IA',
        description=(f"{description}\nSuggestions : {json.dumps(suggestions, ensure_ascii=False)}\n"
                     f"Recommandations : {json.dumps(recommendations, ensure_ascii=False)}\nUrgence : {urgency}"),
        date_evenement=timezone.now(), source_ia=True,
    )
    return Response({
        'id': diagnostic.id, 'photo': request.build_absolute_uri(diagnostic.photo.url),
        'description': diagnostic.description, 'suggestions': diagnostic.suggestions,
        'recommandations': diagnostic.recommandations, 'urgence': diagnostic.urgence,
        'limites': diagnostic.limites, 'date_creation': diagnostic.date_creation,
    }, status=status.HTTP_201_CREATED)
