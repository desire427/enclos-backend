from rest_framework import serializers

from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'nom', 'description', 'prix', 'duree_mois',
            'nb_fermes_max', 'nb_animaux_max', 'acces_ia', 'acces_support', 'acces_analyses'
        ]
