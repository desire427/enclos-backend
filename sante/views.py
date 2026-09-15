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
            qs = qs.filter(ferme__proprietaire=self.request.user)
        else:
            return qs.none()
        animal_id = self.request.query_params.get('animal')
        if animal_id:
            qs = qs.filter(animal_id=animal_id)
        return qs

    def perform_create(self, serializer):
        ferme = self.request.user.fermes.first()
        serializer.save(ferme=ferme)
