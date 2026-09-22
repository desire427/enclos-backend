from rest_framework import serializers
from .models import SuiviSante
from common_validation import reject_future, validate_date_order, validate_non_negative, validate_text


class SuiviSanteSerializer(serializers.ModelSerializer):
    animal_nom = serializers.SerializerMethodField()

    class Meta:
        model = SuiviSante
        fields = [
            'id', 'ferme', 'animal', 'animal_nom',
            'date_debut', 'date_prochaine_consultation', 'date_fin',
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
        reject_future(attrs.get('date_debut'), 'La date de début')
        validate_date_order(attrs, 'date_debut', 'date_prochaine_consultation', 'La prochaine consultation doit être postérieure à la date de début.')
        validate_date_order(attrs, 'date_debut', 'date_fin', 'La date de fin doit être postérieure à la date de début.')
        if attrs.get('poids_kg') is not None:
            validate_non_negative(attrs['poids_kg'], 'Le poids')
        if attrs.get('temperature_celsius') is not None and not 20 <= attrs['temperature_celsius'] <= 50:
            raise serializers.ValidationError({'temperature_celsius': 'La température doit être comprise entre 20 et 50 °C.'})
        if attrs.get('frequence_cardiaque') is not None and not 1 <= attrs['frequence_cardiaque'] <= 500:
            raise serializers.ValidationError({'frequence_cardiaque': 'La fréquence cardiaque doit être comprise entre 1 et 500 bpm.'})
        attrs['note'] = validate_text(attrs.get('note', ''), 'La note', required=False, max_length=4000)
        return attrs

    def get_animal_nom(self, obj):
        if not obj.animal:
            return None
        return obj.animal.nom or obj.animal.numero_identification
