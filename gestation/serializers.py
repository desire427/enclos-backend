from rest_framework import serializers
from .models import Gestation


class GestationSerializer(serializers.ModelSerializer):
    animal_nom = serializers.SerializerMethodField()
    pere_nom   = serializers.SerializerMethodField()

    class Meta:
        model = Gestation
        fields = [
            'id', 'ferme', 'animal', 'animal_nom',
            'pere', 'pere_nom',
            'date_debut', 'date_prevue',
            'date_mise_bas_reelle',
            'duree_jours', 'nombre_naissances',
            'statut', 'note',
            'date_creation', 'date_modification',
        ]
        read_only_fields = ['id', 'ferme', 'date_creation', 'date_modification']

    def get_animal_nom(self, obj):
        if not obj.animal:
            return None
        return obj.animal.nom or obj.animal.numero_identification

    def get_pere_nom(self, obj):
        if not obj.pere:
            return None
        return obj.pere.nom or obj.pere.numero_identification
