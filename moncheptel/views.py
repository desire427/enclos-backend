from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
import base64
from io import BytesIO
from .models import Animal, Race
from .serializers import AnimalSerializer, RaceSerializer


class RaceViewSet(viewsets.ModelViewSet):
    """
    CRUD sur les races.
    GET /api/races/?espece=bovin  → filtre par espèce
    """
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Race.objects.all()
        espece = self.request.query_params.get('espece')
        if espece:
            qs = qs.filter(espece=espece)
        return qs


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.select_related('ferme', 'race').all()
    serializer_class = AnimalSerializer
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.presence != 'present':
            raise ValidationError({'detail': 'Un animal vendu ou mort ne peut plus être modifié.'})
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.presence != 'present':
            raise ValidationError({'detail': 'Un animal vendu ou mort ne peut plus être modifié.'})
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Le numéro d'identification est généré dans Animal.save()
        ferme = self._get_ferme()
        serializer.save(ferme=ferme)

    @action(detail=True, methods=['get'], url_path='qr')
    def qr_code(self, request, pk=None):
        """Génère un QR compact qui permet au scanner Enclos d'ouvrir la fiche."""
        animal = self.get_object()
        encoded = f'ENCLOS1:{animal.id}'
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
        qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=12, border=4)
        qr.add_data(encoded)
        qr.make(fit=True)
        image = qr.make_image(fill_color='black', back_color='white')
        output = BytesIO()
        image.save(output, format='PNG')
        return Response({'animal_id': animal.id, 'qr_data': encoded,
                         'qr_image': 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode()})

    @action(detail=False, methods=['get'], url_path='espece-choices')
    def espece_choices(self, request):
        """Retourne la liste des espèces disponibles (valeur + libellé)."""
        from .models import ESPECE_CHOICES
        return Response([{'value': v, 'label': l} for v, l in ESPECE_CHOICES])
