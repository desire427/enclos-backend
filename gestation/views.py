from rest_framework import viewsets, permissions
from .models import Gestation
from .serializers import GestationSerializer


class GestationViewSet(viewsets.ModelViewSet):
    queryset = Gestation.objects.select_related('ferme', 'animal').all()
    serializer_class = GestationSerializer
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
        # Injecte automatiquement la ferme de l'utilisateur connecté
        ferme = self._get_ferme()
        serializer.save(ferme=ferme)
