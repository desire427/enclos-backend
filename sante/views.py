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
        animal = serializer.validated_data.get('animal')
        if animal.ferme_id != ferme.id:
            raise ValidationError({'animal': 'Cet animal ne fait pas partie de votre ferme.'})
        serializer.save(ferme=ferme)


from .models import Ordonnance
from .ordonnance_serializers import OrdonnanceSerializer
from rest_framework.exceptions import ValidationError


class OrdonnanceViewSet(viewsets.ModelViewSet):
    queryset = Ordonnance.objects.select_related('ferme', 'animal', 'suivi_sante').all()
    serializer_class = OrdonnanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset.filter(ferme__proprietaire=self.request.user)
        animal = self.request.query_params.get('animal')
        if animal:
            qs = qs.filter(animal_id=animal)
        return qs

    def perform_create(self, serializer):
        from fermes.models import Ferme
        ferme_id = self.request.headers.get('X-Ferme-Id') or self.request.query_params.get('ferme_id')
        fermes = Ferme.objects.filter(proprietaire=self.request.user)
        ferme = fermes.filter(id=ferme_id).first() if ferme_id else fermes.first()
        if not ferme:
            raise ValidationError({'ferme': 'Aucune ferme active.'})
        animal = serializer.validated_data.get('animal')
        if animal.ferme_id != ferme.id:
            raise ValidationError({'animal': 'Cet animal ne fait pas partie de votre ferme.'})
        serializer.save(ferme=ferme)
