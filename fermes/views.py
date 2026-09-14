from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Ferme
from .serializers import FermeSerializer
from subscriptions.models import Subscription


class FermeViewSet(viewsets.ModelViewSet):
    queryset = Ferme.objects.select_related('proprietaire').all()
    serializer_class = FermeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ferme.objects.select_related('proprietaire').filter(proprietaire=self.request.user)

    def perform_create(self, serializer):
        subscription = Subscription.objects.filter(
            user=self.request.user,
            statut='active',
            date_fin__gt=timezone.now(),
        ).select_related('plan').order_by('-date_fin').first()

        if not subscription:
            raise PermissionDenied('Un abonnement actif est requis pour créer une ferme.')

        farm_count = self.get_queryset().count()
        if farm_count >= subscription.plan.nb_fermes_max:
            raise PermissionDenied(
                f'Votre forfait {subscription.plan.nom} autorise au maximum {subscription.plan.nb_fermes_max} ferme(s).'
            )
        serializer.save(proprietaire=self.request.user)

    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        farms = self.get_queryset()
        serializer = FermeSerializer(farms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='detail')
    def detail(self, request, pk=None):
        ferm = get_object_or_404(Ferme, pk=pk, proprietaire=request.user)
        serializer = FermeSerializer(ferm)
        return Response(serializer.data)
