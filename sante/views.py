from rest_framework import viewsets, permissions
from .models import SuiviSante
from .serializers import SuiviSanteSerializer


class SuiviSanteViewSet(viewsets.ModelViewSet):
    queryset = SuiviSante.objects.select_related('ferme', 'animal').all()
    serializer_class = SuiviSanteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_ferme(self):
        from fermes.models import Ferme
        ferme_id = self.request.headers.get('X-Ferme-Id') or self.request.query_params.get('ferme_id')
        qs = Ferme.objects.filter(proprietaire=self.request.user)
        if ferme_id:
            return qs.filter(id=ferme_id).first() or qs.first()
        return qs.first()

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        ferme_id = self.request.headers.get('X-Ferme-Id') or self.request.query_params.get('ferme_id')
        if ferme_id:
            qs = self.queryset.filter(ferme__proprietaire=self.request.user, ferme_id=ferme_id)
        else:
            qs = self.queryset.filter(ferme__proprietaire=self.request.user)
        animal_id = self.request.query_params.get('animal')
        if animal_id:
            qs = qs.filter(animal_id=animal_id)
        return qs

    def perform_create(self, serializer):
        ferme = self._get_ferme()
        serializer.save(ferme=ferme)
