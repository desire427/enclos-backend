from rest_framework import serializers
from .models import SuiviSante


class SuiviSanteSerializer(serializers.ModelSerializer):
    animal_nom = serializers.SerializerMethodField()

    class Meta:
        model = SuiviSante
        fields = [
            'id', 'ferme', 'animal', 'animal_nom',
            'date_debut', 'date_prochaine_consultation',
            'statut', 'poids_kg', 'temperature_celsius', 'frequence_cardiaque', 'note',
            'date_creation', 'date_modification',
        ]
        read_only_fields = ['id', 'ferme', 'date_creation', 'date_modification']

    def validate(self, attrs):
        # Autoriser la création sans date de consultation future
        # en gardant la date de début optionnelle si elle est vide.
        if attrs.get('date_debut') in (None, ''):
            attrs['date_debut'] = None
        if attrs.get('date_prochaine_consultation') in (None, ''):
            attrs['date_prochaine_consultation'] = None
        return attrs

    def get_animal_nom(self, obj):
        if not obj.animal:
            return None
        return obj.animal.nom or obj.animal.numero_identification
