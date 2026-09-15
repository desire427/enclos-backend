from rest_framework import viewsets, permissions
from .models import Alerte
from .serializers import AlerteSerializer


class AlerteViewSet(viewsets.ModelViewSet):
    queryset = Alerte.objects.select_related('ferme', 'animal').all()
    serializer_class = AlerteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        if self.request.user.is_authenticated:
            return qs.filter(ferme__proprietaire=self.request.user).order_by('-date_creation')
        return qs.none()
