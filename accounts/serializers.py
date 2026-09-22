from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Role, UserProfile
from common_validation import validate_gps, validate_name, validate_phone, validate_text

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'nom', 'description']


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telephone', 'role', 'date_inscription', 'derniere_connexion', 'actif'
        ]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    password_confirm = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    telephone = serializers.CharField(required=False, allow_blank=True)
    nom_ferme = serializers.CharField(required=False, allow_blank=True)
    localisation = serializers.CharField(required=False, allow_blank=True)
    superficie = serializers.DecimalField(required=False, max_digits=8, decimal_places=2, min_value=0)
    coordonnees_gps = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        attrs['username'] = validate_text(attrs.get('username'), "Le nom d'utilisateur", min_length=2, max_length=150)
        attrs['email'] = attrs['email'].strip().lower()
        attrs['first_name'] = validate_name(attrs.get('first_name', ''), 'Le prénom', required=False, min_length=2, max_length=50)
        attrs['last_name'] = validate_name(attrs.get('last_name', ''), 'Le nom', required=False, min_length=2, max_length=50)
        attrs['telephone'] = validate_phone(attrs.get('telephone', ''))
        attrs['nom_ferme'] = validate_name(attrs.get('nom_ferme', ''), 'Le nom de la ferme', required=False)
        attrs['localisation'] = validate_text(attrs.get('localisation', ''), 'La localisation', required=False, min_length=2, max_length=150)
        attrs['coordonnees_gps'] = validate_gps(attrs.get('coordonnees_gps', ''))
        attrs['description'] = validate_text(attrs.get('description', ''), 'La description', required=False, max_length=2000)
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Les mots de passe ne correspondent pas.'})
        validate_password(attrs['password'])
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'Ce nom d’utilisateur existe déjà.'})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'Cet email est déjà utilisé.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        nom_ferme = validated_data.pop('nom_ferme', '')
        localisation = validated_data.pop('localisation', '')
        superficie = validated_data.pop('superficie', 0)
        coordonnees_gps = validated_data.pop('coordonnees_gps', '')
        description = validated_data.pop('description', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        telephone = validated_data.get('telephone', '')
        profile = UserProfile.objects.create(user=user, telephone=telephone)

        if nom_ferme:
            from fermes.models import Ferme
            Ferme.objects.create(
                nom=nom_ferme,
                localisation=localisation,
                superficie=superficie,
                coordonnees_gps=coordonnees_gps,
                description=description,
                proprietaire=user,
            )

        return user
