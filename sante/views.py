from rest_framework import viewsets, permissions
from .models import SuiviSante
from .serializers import SuiviSanteSerializer


class SuiviSanteViewSet(viewsets.ModelViewSet):
    queryset = SuiviSante.objects.select_related('ferme', 'animal').all()
    serializer_class = SuiviSanteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        if self.request.user.is_authenticated:
            return qs.filter(ferme__proprietaire=self.request.user)
        return qs.none()

    def perform_create(self, serializer):
        ferme = self.request.user.fermes.first()
        serializer.save(ferme=ferme)
