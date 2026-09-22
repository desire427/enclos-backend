from rest_framework import serializers
from .models import Gestation
from common_validation import reject_future, validate_non_negative, validate_text, validate_date_order


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

    def validate(self, attrs):
        date_debut = attrs.get('date_debut')
        date_prevue = attrs.get('date_prevue')
        date_mise_bas = attrs.get('date_mise_bas_reelle')
        reject_future(date_debut, 'La date de saillie')
        validate_date_order(attrs, 'date_debut', 'date_prevue', 'La date prévue doit être postérieure à la date de saillie.')
        validate_date_order(attrs, 'date_debut', 'date_mise_bas_reelle', 'La date de mise bas doit être postérieure à la date de saillie.')
        if 'duree_jours' in attrs:
            validate_non_negative(attrs['duree_jours'], 'La durée', strictly_positive=True)
        if 'nombre_naissances' in attrs and attrs['nombre_naissances'] is not None:
            validate_non_negative(attrs['nombre_naissances'], 'Le nombre de naissances')
        if 'note' in attrs:
            attrs['note'] = validate_text(attrs['note'], 'La note', required=False, max_length=4000)
        return attrs
