"""
API de prédiction IA.

Endpoints :
  POST /api/ia/predire/          — déclenche une prédiction pour un animal donné
  GET  /api/ia/predictions/      — liste toutes les prédictions de la ferme
  GET  /api/ia/predictions/{id}/ — détail d'une prédiction
  GET  /api/ia/predictions/?animal={id} — prédictions d'un animal
"""

import threading

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
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
