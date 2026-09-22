from rest_framework import serializers
from .models import Animal, Race
from common_validation import reject_future, validate_name, validate_non_negative, validate_text


class RaceSerializer(serializers.ModelSerializer):
    def validate_nom(self, value):
        return validate_name(value, 'Le nom de la race')

    def validate_description(self, value):
        return validate_text(value, 'La description', required=False, max_length=2000)

    espece_display = serializers.CharField(source='get_espece_display', read_only=True)

    class Meta:
        model  = Race
        fields = ['id', 'espece', 'espece_display', 'nom', 'description']


class AnimalSerializer(serializers.ModelSerializer):
    race_nom        = serializers.CharField(source='race.nom',               read_only=True, default=None)
    espece_display  = serializers.CharField(source='get_espece_display',     read_only=True)
    sexe_display    = serializers.CharField(source='get_sexe_display',       read_only=True)
    presence_display   = serializers.CharField(source='get_presence_display',   read_only=True)
    etat_sante_display = serializers.CharField(source='get_etat_sante_display', read_only=True)

    class Meta:
        model  = Animal
        fields = [
            'id',
            'ferme',
            'nom',
            'numero_identification',
            'espece',
            'espece_display',
            'race',
            'race_nom',
            'sexe',
            'sexe_display',
            'date_naissance',
            'date_arrivee',
            'date_depart',
            'poids_naissance',
            'presence',
            'presence_display',
            'etat_sante',
            'etat_sante_display',
            'couleur',
            'observations',
            'date_creation',
            'date_modification',
        ]
        read_only_fields = [
            'id',
            'numero_identification',
            'ferme',
            'date_creation',
            'date_modification',
        ]

    def validate_nom(self, value):
        return validate_name(value, "Le nom de l'animal", required=False, min_length=2)

    def validate_date_naissance(self, value):
        return reject_future(value, 'La date de naissance')

    def validate_poids_naissance(self, value):
        return validate_non_negative(value, 'Le poids')

    def validate_couleur(self, value):
        return validate_text(value, 'La couleur', required=False, min_length=2, max_length=80)

    def validate_observations(self, value):
        return validate_text(value, 'Les observations', required=False, max_length=4000)
