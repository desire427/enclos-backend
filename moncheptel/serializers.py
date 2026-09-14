from rest_framework import serializers
from .models import Animal, Race


class RaceSerializer(serializers.ModelSerializer):
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
