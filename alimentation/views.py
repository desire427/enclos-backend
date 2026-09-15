from rest_framework import viewsets, permissions
from .models import Alimentation, TypeAliment, FrequenceAlimentation
from .serializers import (
    AlimentationSerializer,
    TypeAlimentSerializer,
    FrequenceAlimentationSerializer,
)


class TypeAlimentViewSet(viewsets.ModelViewSet):
    """CRUD sur les types d'aliment — partagés entre tous les utilisateurs."""
    queryset           = TypeAliment.objects.all()
    serializer_class   = TypeAlimentSerializer
    permission_classes = [permissions.IsAuthenticated]


class FrequenceAlimentationViewSet(viewsets.ModelViewSet):
    """CRUD sur les fréquences d'alimentation."""
    queryset           = FrequenceAlimentation.objects.all()
    serializer_class   = FrequenceAlimentationSerializer
    permission_classes = [permissions.IsAuthenticated]


class AlimentationViewSet(viewsets.ModelViewSet):
    queryset           = Alimentation.objects.select_related('ferme', 'animal', 'type_aliment', 'frequence').all()
    serializer_class   = AlimentationSerializer
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
        ferme = self._get_ferme()
        serializer.save(ferme=ferme)
