import base64
import json
import re
from datetime import date

import requests
from rest_framework import viewsets, permissions
from rest_framework import status
from rest_framework.decorators import action, api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from .models import SuiviSante
from .serializers import SuiviSanteSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def extraire_ordonnance(request):
    """Extrait les champs lisibles d'une photo d'ordonnance sans l'enregistrer."""
    from django.conf import settings

    image = request.FILES.get('photo')
    if not image:
        return Response({'detail': 'Ajoutez une photo de l’ordonnance.'}, status=status.HTTP_400_BAD_REQUEST)
    if image.size > 8 * 1024 * 1024:
        return Response({'detail': 'La photo ne peut pas dépasser 8 Mo.'}, status=status.HTTP_400_BAD_REQUEST)
    if image.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        return Response({'detail': 'Formats acceptés : JPEG, PNG ou WebP.'}, status=status.HTTP_400_BAD_REQUEST)
    if not settings.GEMINI_API_KEY:
        return Response({'detail': 'L’extraction OCR n’est pas configurée : ajoutez GEMINI_API_KEY au fichier .env.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        from PIL import Image
        from PIL import ImageStat
        checked_image = Image.open(image)
        checked_image.verify()
        image.seek(0)
        checked_image = Image.open(image).convert('L')
        checked_image.thumbnail((256, 256))
        image_stats = ImageStat.Stat(checked_image)
        darkest, brightest = checked_image.getextrema()
        dark_pixel_ratio = sum(checked_image.histogram()[:12]) / (checked_image.width * checked_image.height)
        if brightest - darkest < 8 or (image_stats.mean[0] < 18 and dark_pixel_ratio > 0.98):
            return Response(
                {'detail': 'La photo est trop sombre, uniforme ou ne contient pas de texte lisible. Reprenez l’ordonnance avec un bon éclairage.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        image.seek(0)
        encoded_image = base64.b64encode(image.read()).decode('ascii')
    except Exception:
        return Response({'detail': 'Le fichier fourni ne contient pas une image valide.'}, status=status.HTTP_400_BAD_REQUEST)

    prompt = (
        "Transcris cette ordonnance vétérinaire et extrais les champs sans rien inventer. "
        "Recopie fidèlement les noms de médicaments, dosages, fréquences, durées, voies d’administration et instructions lisibles. "
        "Regroupe chaque médicament et sa posologie dans le champ medicaments, une ligne par médicament; mets les consignes générales "
        "dans instructions. Utilise le format de date YYYY-MM-DD uniquement si la date est lisible et non ambiguë; sinon laisse la date vide. "
        "Si l’image est noire, vide, sans écriture ou ne montre pas une ordonnance vétérinaire, ne devine aucun contenu et indique "
        "texte_ordonnance_detecte à false. Pour une vraie ordonnance, mets texte_ordonnance_detecte à true. "
        "Si le titre, le nom du vétérinaire ou un texte est absent ou illisible, renvoie une chaîne vide pour ce champ. "
        "Réponds uniquement en JSON avec les champs texte_ordonnance_detecte, titre, veterinaire, date_prescription, medicaments et instructions."
    )
    try:
        response = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_VISION_MODEL}:generateContent',
            headers={'x-goog-api-key': settings.GEMINI_API_KEY}, timeout=(10, 60),
            json={
                'contents': [{'parts': [
                    {'text': prompt},
                    {'inline_data': {'mime_type': image.content_type, 'data': encoded_image}},
                ]}],
                'generationConfig': {'temperature': 0, 'responseMimeType': 'application/json'},
            },
        )
        response.raise_for_status()
        extracted = json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
        if not isinstance(extracted, dict):
            raise ValueError('La réponse OCR doit être un objet JSON.')
        fields = ('titre', 'veterinaire', 'date_prescription', 'medicaments', 'instructions')
        data = {field: str(extracted.get(field) or '').strip() for field in fields}
        if extracted.get('texte_ordonnance_detecte') is not True or not any(
            data[field] for field in ('titre', 'medicaments', 'instructions')
        ):
            return Response(
                {'detail': 'Aucune écriture d’ordonnance lisible n’a été détectée. Prenez une photo nette de l’ordonnance.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if data['date_prescription']:
            try:
                date.fromisoformat(data['date_prescription'])
            except ValueError:
                data['date_prescription'] = ''
        data['informations_a_verifier'] = [field for field in fields if not data[field]]
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        return Response({'detail': 'L’extraction de l’ordonnance est indisponible. Réessayez avec une photo plus nette.'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response(data, status=status.HTTP_200_OK)


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

    @action(detail=True, methods=['post'], url_path=r'traitements/(?P<traitement_id>[^/.]+)/terminer')
    def terminer_traitement(self, request, pk=None, traitement_id=None):
        from django.db import transaction
        from django.utils import timezone
        from alertes.models import Alerte
        from .models import TraitementOrdonnance

        ordonnance = self.get_object()
        try:
            traitement = TraitementOrdonnance.objects.get(
                pk=traitement_id, ordonnance=ordonnance,
            )
        except (TraitementOrdonnance.DoesNotExist, TypeError, ValueError):
            return Response({'detail': 'Médicament introuvable dans cette ordonnance.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            traitement.actif = False
            traitement.save(update_fields=['actif'])
            traitement.rappels.filter(actif=True).update(actif=False)
            Alerte.objects.filter(
                rappel_ordonnance__traitement=traitement,
                statut__in=['non_lue', 'Non lue'],
            ).update(statut='lue', date_modification=timezone.now())

        ordonnance.refresh_from_db()
        return Response(self.get_serializer(ordonnance).data)
