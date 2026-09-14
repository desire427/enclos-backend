from rest_framework import serializers
from .models import HistoriqueEvenement


class HistoriqueEvenementSerializer(serializers.ModelSerializer):
    # Champs lecture seule utiles pour le frontend
    animal_nom = serializers.SerializerMethodField()

    class Meta:
        model  = HistoriqueEvenement
        fields = [
            'id',
            'ferme',
            'animal',
            'animal_nom',
            'type_evenement',
            'titre',
            'description',
            'date_evenement',
            'source_ia',
            'date_creation',
        ]
        read_only_fields = ['id', 'date_creation', 'animal_nom']

    def get_animal_nom(self, obj):
        if not obj.animal:
            return None
        return obj.animal.nom or obj.animal.numero_identification
