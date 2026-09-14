from rest_framework import viewsets, permissions
from .models import HistoriqueEvenement
from .serializers import HistoriqueEvenementSerializer


class HistoriqueEvenementViewSet(viewsets.ModelViewSet):
    queryset = HistoriqueEvenement.objects.select_related('ferme', 'animal').order_by('-date_evenement')
    serializer_class   = HistoriqueEvenementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        if not self.request.user.is_authenticated:
            return qs.none()

        qs = qs.filter(ferme__proprietaire=self.request.user)

        # Filtre optionnel par animal : GET /api/historiques/?animal=5
        animal_id = self.request.query_params.get('animal')
        if animal_id:
            qs = qs.filter(animal_id=animal_id)

        # Filtre optionnel par type : GET /api/historiques/?type=Alimentation
        type_ev = self.request.query_params.get('type')
        if type_ev:
            qs = qs.filter(type_evenement__icontains=type_ev)

        return qs
