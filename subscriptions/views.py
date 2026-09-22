import decimal
import calendar
import json

import requests
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from plans.models import Plan
from .models import Subscription
from .serializers import SubscriptionSerializer
from accounts.serializers import RegisterSerializer
from common_validation import validate_phone


def _find_paydunya_checkout_url(payload):
    keys = ('response_text', 'response_url', 'checkout_url', 'invoice_url', 'url', 'payment_url', 'link')

    def walk(node):
        if isinstance(node, dict):
            for key in keys:
                if key in node:
                    value = node[key]
                    if isinstance(value, str) and value.strip().startswith(('http://', 'https://')):
                        return value
            for value in node.values():
                found = walk(value)
                if found:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = walk(item)
                if found:
                    return found
        return None

    return walk(payload)


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _activate_subscription(subscription, payload):
    paid_at = timezone.now()
    subscription.statut = 'active'
    subscription.date_debut = paid_at
    subscription.date_paiement = paid_at
    subscription.date_fin = _add_months(paid_at, subscription.plan.duree_mois)
    subscription.receipt_url = payload.get('receipt_url', '') or subscription.receipt_url
    subscription.moyen_paiement = (
        payload.get('payment_method', '')
        or payload.get('channel', '')
        or subscription.moyen_paiement
    )
    subscription.save()
    return subscription


def _complete_pending_registration(subscription, payload):
    if subscription.user_id:
        return subscription

    registration = subscription.inscription_en_attente or {}
    if not registration:
        return subscription

    serializer = RegisterSerializer(data=registration)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        user = serializer.save()
        subscription.user = user
        subscription.inscription_en_attente = {}
        subscription.save(update_fields=['user', 'inscription_en_attente'])
    return subscription


def _authentication_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@api_view(['GET', 'POST'])
@authentication_classes([])
@permission_classes([])
def paydunya_callback(request):
    payload = request.data.get('data', request.data)
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = request.data

    invoice = payload.get('invoice', {}) if isinstance(payload, dict) else {}
    token = invoice.get('token') or payload.get('token') if isinstance(payload, dict) else None
    status_value = (payload.get('status') or payload.get('state') or '').strip().lower() if isinstance(payload, dict) else ''

    if status_value in ('success', 'completed'):
        subscription = Subscription.objects.filter(paydunya_token=token).order_by('-id').first()
        if not subscription:
            return Response({'detail': 'Facture PayDunya introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        _complete_pending_registration(subscription, payload)
        _activate_subscription(subscription, payload)
        return Response({
            'message': 'Paiement validé avec succès. Votre abonnement est activé.'
        }, status=status.HTTP_200_OK)

    if status_value in ('cancel', 'cancelled', 'failed'):
        Subscription.objects.filter(paydunya_token=token, statut='pending').update(statut='cancelled')
        return Response({
            'message': 'Paiement annulé. Le paiement n’a pas été validé.'
        }, status=status.HTTP_200_OK)

    return Response({
        'message': 'Paiement PayDunya reçu, mais aucun statut de succès ou d’annulation n’a été fourni.'
    }, status=status.HTTP_200_OK)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        sub = self.get_queryset().filter(
            statut='active',
            date_fin__gt=timezone.now(),
        ).order_by('-date_fin', '-id').first()
        if not sub:
            from rest_framework.exceptions import NotFound
            raise NotFound('Aucun abonnement actif trouvé.')
        serializer = self.get_serializer(sub)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='confirm-paydunya', permission_classes=[permissions.AllowAny])
    def confirm_paydunya(self, request):
        invoice_token = request.data.get('token')
        if not invoice_token:
            return Response({'detail': 'Le token PayDunya est requis.'}, status=status.HTTP_400_BAD_REQUEST)

        subscription_queryset = Subscription.objects.all() if not request.user.is_authenticated else self.get_queryset()
        subscription = get_object_or_404(subscription_queryset, paydunya_token=invoice_token)
        endpoint = getattr(settings, 'PAYDUNYA_ENDPOINT', '').replace('/create', f'/confirm/{invoice_token}')
        headers = {
            'Content-Type': 'application/json',
            'PAYDUNYA-MASTER-KEY': getattr(settings, 'PAYDUNYA_MASTER_KEY', ''),
            'PAYDUNYA-PRIVATE-KEY': getattr(settings, 'PAYDUNYA_PRIVATE_KEY', ''),
            'PAYDUNYA-TOKEN': getattr(settings, 'PAYDUNYA_TOKEN', ''),
        }
        try:
            response = requests.get(endpoint, headers=headers, timeout=30)
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            return Response({'detail': f'Impossible de vérifier le paiement PayDunya : {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        if response.status_code >= 400 or payload.get('response_code') != '00':
            return Response({'detail': payload.get('response_text', 'Vérification PayDunya impossible.')}, status=status.HTTP_400_BAD_REQUEST)

        payment_status = str(payload.get('status', '')).lower()
        if payment_status == 'completed':
            _complete_pending_registration(subscription, payload)
            subscription = _activate_subscription(subscription, payload)
        elif payment_status in ('cancelled', 'failed'):
            subscription.statut = 'cancelled'
            subscription.save(update_fields=['statut'])

        response_data = self.get_serializer(subscription).data
        if subscription.user_id and not request.user.is_authenticated:
            response_data['auth'] = _authentication_payload(subscription.user)
        return Response(response_data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def paydunya(self, request):
        plan_id = request.data.get('plan')
        amount = request.data.get('montant_paye')
        operator = request.data.get('operator') or 'Mobile'
        if operator not in ('wave', 'orange', 'Mobile'):
            return Response({'detail': 'Le moyen de paiement sélectionné est invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        phone = request.data.get('phone') or ''
        if phone:
            try:
                phone = validate_phone(phone, required=True)
            except serializers.ValidationError as exc:
                return Response({'detail': exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        if not plan_id:
            return Response({'detail': 'Le plan est requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            return Response({'detail': 'Forfait introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if not amount:
            amount = str(plan.prix)

        try:
            amount_decimal = decimal.Decimal(str(amount))
        except Exception:
            return Response({'detail': 'Le montant du paiement est invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        registration = request.data.get('registration') or {}
        if not request.user.is_authenticated:
            registration_serializer = RegisterSerializer(data=registration)
            registration_serializer.is_valid(raise_exception=True)

        payload = {
            'invoice': {
                'total_amount': f'{amount_decimal:.2f}',
                'description': f'Abonnement {plan.nom}',
                'customer': {
                        'name': (request.user.get_full_name() or request.user.username) if request.user.is_authenticated else f"{registration.get('first_name', '')} {registration.get('last_name', '')}".strip(),
                        'email': request.user.email if request.user.is_authenticated else registration.get('email', ''),
                    'phone': phone,
                },
            },
            'store': {'name': 'Enclos'},
            'actions': {
                'return_url': getattr(settings, 'PAYDUNYA_RETURN_URL', 'http://127.0.0.1:5173/paiement'),
                'cancel_url': getattr(settings, 'PAYDUNYA_CANCEL_URL', 'http://127.0.0.1:5173/paiement?cancel=1'),
                'callback_url': getattr(settings, 'PAYDUNYA_CALLBACK_URL', 'http://127.0.0.1:8000/api/subscriptions/paydunya/callback/'),
            },
        }

        api_key = getattr(settings, 'PAYDUNYA_MASTER_KEY', '')
        private_key = getattr(settings, 'PAYDUNYA_PRIVATE_KEY', '')
        token = getattr(settings, 'PAYDUNYA_TOKEN', '')
        if not api_key or not private_key or not token:
            return Response({
                'detail': 'Les identifiants PayDunya de test ne sont pas encore configurés dans l’environnement Django.',
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'Content-Type': 'application/json',
            'PAYDUNYA-MASTER-KEY': api_key,
            'PAYDUNYA-PRIVATE-KEY': private_key,
            'PAYDUNYA-TOKEN': token,
        }

        endpoint = getattr(settings, 'PAYDUNYA_ENDPOINT', 'https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create')
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            payload_json = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
        except Exception as exc:
            return Response({'detail': f'PayDunya inconnu: {str(exc)}'}, status=status.HTTP_502_BAD_GATEWAY)

        if response.status_code >= 400:
            message = (
                payload_json.get('message')
                if isinstance(payload_json, dict)
                else None
            ) or payload_json.get('detail') if isinstance(payload_json, dict) else None
            return Response({'detail': message or response.text or 'Erreur PayDunya.'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload_json, dict) or payload_json.get('response_code') != '00':
            message = payload_json.get('response_text') if isinstance(payload_json, dict) else None
            return Response({
                'detail': message or 'PayDunya a refusé la création de la facture.',
                'payload': payload_json,
            }, status=status.HTTP_400_BAD_REQUEST)

        checkout_url = _find_paydunya_checkout_url(payload_json)
        if not checkout_url:
            return Response({
                'detail': 'PayDunya a accepté la demande mais n’a pas renvoyé l’URL de paiement.',
                'payload': payload_json,
            }, status=status.HTTP_502_BAD_GATEWAY)

        Subscription.objects.create(
            user=request.user if request.user.is_authenticated else None,
            plan=plan,
            statut='pending',
            montant_paye=amount_decimal,
            paydunya_token=payload_json.get('token'),
            moyen_paiement=operator,
            inscription_en_attente=registration if not request.user.is_authenticated else {},
        )

        return Response({
            'checkout_url': checkout_url,
            'invoice': payload_json,
            'plan_id': plan.id,
            'plan_name': plan.nom,
            'amount': f'{amount_decimal:.2f}',
        }, status=status.HTTP_201_CREATED)
