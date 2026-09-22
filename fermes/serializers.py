from rest_framework import serializers

from .models import Ferme
from common_validation import validate_gps, validate_name, validate_text, validate_non_negative


class FermeSerializer(serializers.ModelSerializer):
    def validate_nom(self, value):
        return validate_name(value, 'Le nom de la ferme')

    def validate_localisation(self, value):
        return validate_text(value, 'La localisation', required=True, min_length=2, max_length=150)

    def validate_superficie(self, value):
        return validate_non_negative(value, 'La superficie')

    def validate_coordonnees_gps(self, value):
        return validate_gps(value)

    def validate_description(self, value):
        return validate_text(value, 'La description', required=False, max_length=2000)

    class Meta:
        model = Ferme
        fields = [
            'id', 'nom', 'localisation', 'superficie',
            'coordonnees_gps', 'description', 'proprietaire', 'date_creation'
        ]
        read_only_fields = ['id', 'proprietaire', 'date_creation']
