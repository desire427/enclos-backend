from rest_framework import serializers
from .models import PredictionResultat


class PredictionResultatSerializer(serializers.ModelSerializer):
    animal_nom = serializers.SerializerMethodField()

    class Meta:
        model  = PredictionResultat
        fields = [
            'id', 'animal', 'animal_nom', 'declencheur',
            'est_malade', 'probabilite',
            'shap_values', 'features_used',
            'comparaison_historique',
            'explication_llm', 'envoye_n8n',
            'date_prediction',
        ]
        read_only_fields = fields

    def get_animal_nom(self, obj):
        return obj.animal.nom or obj.animal.numero_identification
