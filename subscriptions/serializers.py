from rest_framework import serializers

from .models import Subscription
from plans.models import Plan


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all())

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'date_debut', 'date_fin',
            'statut', 'montant_paye', 'date_paiement', 'paydunya_token',
            'receipt_url', 'moyen_paiement'
        ]
        read_only_fields = ['user', 'paydunya_token', 'receipt_url', 'moyen_paiement']
