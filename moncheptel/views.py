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

    def _get_ferme(self):
        from fermes.models import Ferme
        ferme_id = self.request.headers.get('X-Ferme-Id') or self.request.query_params.get('ferme_id')
        qs = Ferme.objects.filter(proprietaire=self.request.user)
        if ferme_id:
            return qs.filter(id=ferme_id).first() or qs.first()
        return qs.first()

    def get_queryset(self):
        qs = self.queryset
        if self.request.user.is_authenticated:
            ferme_id = self.request.headers.get('X-Ferme-Id') or self.request.query_params.get('ferme_id')
            if ferme_id:
                return qs.filter(ferme__proprietaire=self.request.user, ferme_id=ferme_id)
            return qs.filter(ferme__proprietaire=self.request.user)
        return qs.none()

    def perform_create(self, serializer):
        # Le numéro d'identification est généré dans Animal.save()
        ferme = self._get_ferme()
        serializer.save(ferme=ferme)

    @action(detail=False, methods=['get'], url_path='espece-choices')
    def espece_choices(self, request):
        """Retourne la liste des espèces disponibles (valeur + libellé)."""
        from .models import ESPECE_CHOICES
        return Response([{'value': v, 'label': l} for v, l in ESPECE_CHOICES])
