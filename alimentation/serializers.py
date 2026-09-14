from rest_framework import serializers
from .models import Alimentation, TypeAliment, FrequenceAlimentation


class TypeAlimentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TypeAliment
        fields = ['id', 'nom', 'description']


class FrequenceAlimentationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FrequenceAlimentation
        fields = ['id', 'nom', 'description']


class AlimentationSerializer(serializers.ModelSerializer):
    # Champs lecture seule pour afficher les libellés
    type_aliment_nom = serializers.CharField(
        source='type_aliment.nom', read_only=True, default=None,
    )
    frequence_nom = serializers.CharField(
        source='frequence.nom', read_only=True, default=None,
    )

    class Meta:
        model  = Alimentation
        fields = [
            'id', 'ferme', 'animal',
            'type_aliment',      # ID pour l'écriture
            'type_aliment_nom',  # libellé pour la lecture
            'frequence',         # ID pour l'écriture
            'frequence_nom',     # libellé pour la lecture
            'quantite_kg',
            'date_alimentation',
            'note',
            'date_creation',
            'date_modification',
        ]
        read_only_fields = ['id', 'ferme', 'date_creation', 'date_modification']
