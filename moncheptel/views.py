from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
import base64, gzip, json
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
        """QR unique contenant la fiche et l'historique compressés (format ENCLOS1)."""
        animal = self.get_object()
        def iso(value):
            return value.isoformat() if value else None
        payload = {
            'format': 'ENCLOS1',
            'animal': {
                'id': animal.id, 'identifiant': animal.numero_identification,
                'nom': animal.nom, 'espece': animal.espece,
                'race': animal.race.nom if animal.race else None,
                'sexe': animal.sexe, 'date_naissance': iso(animal.date_naissance),
                'date_arrivee': iso(animal.date_arrivee), 'date_depart': iso(animal.date_depart),
                'poids_naissance_kg': str(animal.poids_naissance),
                'poids_actuel_kg': str(animal.poids_actuel), 'presence': animal.presence,
                'etat_sante': animal.etat_sante, 'couleur': animal.couleur,
                'observations': animal.observations,
                'photo': request.build_absolute_uri(animal.photo.url) if animal.photo else None,
                'date_creation': iso(animal.date_creation), 'date_modification': iso(animal.date_modification),
            },
            'historique': list(animal.historique_evenements.order_by('date_evenement').values(
                'type_evenement', 'titre', 'description', 'date_evenement', 'source_ia')),
            'suivis_sante': list(animal.sante_suivis.order_by('date_creation').values(
                'date_debut', 'date_prochaine_consultation', 'date_fin', 'statut', 'poids_kg',
                'temperature_celsius', 'frequence_cardiaque', 'note')),
            'ordonnances': [{
                'titre': ordonnance.titre, 'veterinaire': ordonnance.veterinaire,
                'date_prescription': ordonnance.date_prescription, 'medicaments': ordonnance.medicaments,
                'instructions': ordonnance.instructions,
                'document': request.build_absolute_uri(ordonnance.document.url) if ordonnance.document else None,
            } for ordonnance in animal.ordonnances.order_by('date_prescription')],
            'alimentations': list(animal.alimentations.order_by('date_alimentation').values()),
            'gestations': list(animal.gestations.order_by('date_creation').values()),
            'pre_diagnostics': [{
                'photo': request.build_absolute_uri(diagnostic.photo.url) if diagnostic.photo else None,
                'description': diagnostic.description, 'suggestions': diagnostic.suggestions,
                'recommandations': diagnostic.recommandations, 'urgence': diagnostic.urgence,
                'limites': diagnostic.limites, 'date_creation': diagnostic.date_creation,
            } for diagnostic in animal.pre_diagnostics.order_by('date_creation')],
            'predictions_ia': list(animal.predictions.order_by('date_prediction').values(
                'est_malade', 'probabilite', 'explication_llm', 'date_prediction')),
        }
        raw = json.dumps(payload, ensure_ascii=False, default=str, separators=(',', ':')).encode()
        encoded = 'ENCLOS1:' + base64.urlsafe_b64encode(gzip.compress(raw, compresslevel=9)).decode().rstrip('=')
        import qrcode
        from qrcode.constants import ERROR_CORRECT_L
        qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_L, box_size=7, border=3)
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
