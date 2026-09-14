from rest_framework import viewsets, permissions
from .models import Gestation
from .serializers import GestationSerializer


class GestationViewSet(viewsets.ModelViewSet):
    queryset = Gestation.objects.select_related('ferme', 'animal').all()
    serializer_class = GestationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        if self.request.user.is_authenticated:
            return qs.filter(ferme__proprietaire=self.request.user)
        return qs.none()

    def perform_create(self, serializer):
        # Injecte automatiquement la ferme de l'utilisateur connecté
        ferme = self.request.user.fermes.first()
        serializer.save(ferme=ferme)
