from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Animal, Race
from .serializers import AnimalSerializer, RaceSerializer


class RaceViewSet(viewsets.ModelViewSet):
    """
    CRUD sur les races.
    GET /api/races/?espece=bovin  → filtre par espèce
    """
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Race.objects.all()
        espece = self.request.query_params.get('espece')
        if espece:
            qs = qs.filter(espece=espece)
        return qs


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.select_related('ferme', 'race').all()
    serializer_class = AnimalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        if self.request.user.is_authenticated:
            return qs.filter(ferme__proprietaire=self.request.user)
        return qs.none()

    def perform_create(self, serializer):
        # Le numéro d'identification est généré dans Animal.save()
        ferme = self.request.user.fermes.first()
        serializer.save(ferme=ferme)

    @action(detail=False, methods=['get'], url_path='espece-choices')
    def espece_choices(self, request):
        """Retourne la liste des espèces disponibles (valeur + libellé)."""
        from .models import ESPECE_CHOICES
        return Response([{'value': v, 'label': l} for v, l in ESPECE_CHOICES])
