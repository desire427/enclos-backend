from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Alerte
from .serializers import AlerteSerializer


class AlerteViewSet(viewsets.ModelViewSet):
    queryset = Alerte.objects.select_related('ferme', 'animal').all()
    serializer_class = AlerteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset
        if self.request.user.is_authenticated:
            ferme_id = self.request.headers.get('X-Ferme-Id') or self.request.query_params.get('ferme_id')
            if ferme_id:
                return qs.filter(ferme__proprietaire=self.request.user, ferme_id=ferme_id).order_by('-date_creation')
            return qs.filter(ferme__proprietaire=self.request.user).order_by('-date_creation')
        return qs.none()

    @action(detail=True, methods=['post'])
    def confirmer(self, request, pk=None):
        alerte = self.get_object()
        if not alerte.rappel_ordonnance_id:
            return Response({'detail': 'Cette alerte ne correspond pas à un rappel de prise.'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        with transaction.atomic():
            rappel = alerte.rappel_ordonnance.__class__.objects.select_for_update().get(
                pk=alerte.rappel_ordonnance_id,
            )
            if not rappel.actif:
                return Response({'detail': 'Ce rappel est déjà terminé.'}, status=status.HTTP_409_CONFLICT)
            if rappel.intervalle_minutes:
                prochaine_prise = rappel.date_prochaine_prise + timedelta(minutes=rappel.intervalle_minutes)
                if rappel.date_fin and prochaine_prise > rappel.date_fin:
                    rappel.actif = False
                else:
                    rappel.date_prochaine_prise = prochaine_prise
                    rappel.dernier_rappel = None
            else:
                rappel.actif = False
            rappel.save(update_fields=['actif', 'date_prochaine_prise', 'dernier_rappel'])
            alerte.__class__.objects.filter(
                rappel_ordonnance=rappel, statut__in=['non_lue', 'Non lue'],
            ).update(statut='lue', date_modification=now)
            alerte.refresh_from_db()

        return Response(self.get_serializer(alerte).data)
