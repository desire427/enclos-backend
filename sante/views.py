import base64
import json
import logging
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

logger = logging.getLogger(__name__)


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
        "Transcris cette ordonnance vétérinaire, y compris les maquettes et ordonnances fictives utilisées pour tester un logiciel, "
        "et extrais les champs sans rien inventer. La mention TEST, FICTIF ou DEMONSTRATION ne rend pas le document illisible : "
        "recopie ces mentions si elles font partie du titre, mais extrais aussi les médicaments et consignes visibles. "
        "Recopie fidèlement les noms de médicaments, dosages, fréquences, durées, voies d’administration et instructions lisibles. "
        "Regroupe chaque médicament et sa posologie dans le champ medicaments, une ligne par médicament; mets les consignes générales "
        "dans instructions. Utilise le format de date YYYY-MM-DD uniquement si la date est lisible et non ambiguë; sinon laisse la date vide. "
        "Mets texte_ordonnance_detecte à true dès qu'une prescription, une maquette de prescription ou un exemple de prescription "
        "est visible avec au moins un médicament ou une consigne de traitement. Mets ce champ à false uniquement si l’image est noire, "
        "vide, sans écriture lisible ou ne contient aucun élément de prescription. Ne devine jamais le texte manquant. "
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
        has_prescription_content = bool(data['medicaments'] or data['instructions'])
        if not has_prescription_content:
            logger.info(
                'Gemini ordonnance OCR found no prescription content (detected=%s).',
                extracted.get('texte_ordonnance_detecte'),
            )
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
    except requests.HTTPError as exc:
        upstream_status = exc.response.status_code if exc.response is not None else None
        logger.warning('Gemini ordonnance OCR rejected the request (HTTP %s).', upstream_status)
        if upstream_status in (401, 403):
            return Response(
                {'detail': 'Le service OCR a refusé la clé Gemini. Vérifiez GEMINI_API_KEY dans backend/.env.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if upstream_status == 429:
            return Response(
                {'detail': 'Le quota du service OCR est atteint. Réessayez plus tard ou vérifiez le quota Gemini.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {'detail': 'Le service OCR a refusé la requête. Vérifiez le modèle Gemini et réessayez.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except requests.Timeout:
        logger.warning('Gemini ordonnance OCR request timed out.')
        return Response(
            {'detail': 'Le service OCR met trop de temps à répondre. Réessayez dans quelques instants.'},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning('Gemini ordonnance OCR request failed (%s).', type(exc).__name__)
        return Response(
            {'detail': 'Impossible de joindre le service OCR. Vérifiez la connexion Internet du backend et réessayez.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        logger.warning('Gemini ordonnance OCR returned an invalid response (%s).', type(exc).__name__)
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
