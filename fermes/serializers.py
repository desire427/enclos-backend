from rest_framework import serializers

from .models import Ferme


class FermeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ferme
        fields = [
            'id', 'nom', 'localisation', 'superficie',
            'coordonnees_gps', 'description', 'proprietaire', 'date_creation'
        ]
        read_only_fields = ['id', 'proprietaire', 'date_creation']
