from rest_framework import serializers
from common_validation import validate_text
from .models import Ordonnance


class OrdonnanceSerializer(serializers.ModelSerializer):
    animal_nom = serializers.SerializerMethodField()

    class Meta:
        model = Ordonnance
        fields = ['id', 'ferme', 'animal', 'animal_nom', 'suivi_sante', 'titre', 'veterinaire', 'date_prescription', 'medicaments', 'instructions', 'document', 'date_creation', 'date_modification']
        read_only_fields = ['id', 'ferme', 'date_creation', 'date_modification']

    def validate(self, attrs):
        animal = attrs.get('animal') or (self.instance.animal if self.instance else None)
        if animal and animal.presence != 'present':
            raise serializers.ValidationError({'animal': 'Impossible de modifier ou ajouter une ordonnance pour un animal vendu ou mort.'})
        for key, label, maximum in [('titre', 'Le titre', 150), ('medicaments', 'Les médicaments', 5000), ('instructions', 'Les instructions', 5000), ('veterinaire', 'Le nom du vétérinaire', 150)]:
            value = attrs.get(key, getattr(self.instance, key, '') if self.instance else '')
            attrs[key] = validate_text(value, label, required=(key in ('titre', 'medicaments')), max_length=maximum)
        return attrs

    def get_animal_nom(self, obj):
        return obj.animal.nom or obj.animal.numero_identification
