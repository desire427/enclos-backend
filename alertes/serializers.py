from rest_framework import serializers
from .models import Alerte


class AlerteSerializer(serializers.ModelSerializer):
    animal_identification = serializers.CharField(
        source='animal.numero_identification', read_only=True, default=None
    )
    animal_nom = serializers.CharField(source='animal.nom', read_only=True, default=None)
    rappel_actif = serializers.SerializerMethodField()

    class Meta:
        model = Alerte
        fields = [
            'id', 'ferme', 'animal', 'animal_identification', 'animal_nom', 'type_alerte', 'message',
            'rappel_ordonnance', 'rappel_actif', 'statut', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']

    def get_rappel_actif(self, obj):
        return bool(obj.rappel_ordonnance_id and obj.rappel_ordonnance.actif)
