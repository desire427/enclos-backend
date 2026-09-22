from rest_framework import serializers
from .models import Alimentation, TypeAliment, FrequenceAlimentation
from common_validation import reject_future, validate_name, validate_non_negative, validate_text


class TypeAlimentSerializer(serializers.ModelSerializer):
    def validate_nom(self, value):
        return validate_name(value, "Le nom du type d'aliment")

    def validate_description(self, value):
        return validate_text(value, 'La description', required=False, max_length=2000)

    class Meta:
        model  = TypeAliment
        fields = ['id', 'nom', 'description']


class FrequenceAlimentationSerializer(serializers.ModelSerializer):
    def validate_nom(self, value):
        return validate_name(value, 'Le nom de la fréquence')

    def validate_description(self, value):
        return validate_text(value, 'La description', required=False, max_length=2000)

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

    def validate_quantite_kg(self, value):
        return validate_non_negative(value, 'La quantité', strictly_positive=True)

    def validate_date_alimentation(self, value):
        return reject_future(value, "La date d'alimentation")

    def validate_note(self, value):
        return validate_text(value, 'La note', required=False, max_length=2000)
