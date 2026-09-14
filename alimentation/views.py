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

    def get_queryset(self):
        qs = self.queryset
        if self.request.user.is_authenticated:
            return qs.filter(ferme__proprietaire=self.request.user)
        return qs.none()

    def perform_create(self, serializer):
        ferme = self.request.user.fermes.first()
        serializer.save(ferme=ferme)
