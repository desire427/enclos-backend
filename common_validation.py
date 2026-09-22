import re
from datetime import date
from decimal import Decimal

from rest_framework import serializers


NAME_PATTERN = re.compile(r"^[^\W\d_][\w\s'’-]*$", re.UNICODE)
EMAIL_MAX_LENGTH = 254
PHONE_PATTERN = re.compile(r"^(?:7[05678]\d{7}|[235]\d{8})$")
GPS_PATTERN = re.compile(r"^\s*(-?\d{1,3}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$")


def clean_text(value):
    if value is None:
        return value
    return ' '.join(str(value).split()).strip()


def validate_text(value, label, *, required=True, min_length=1, max_length=None):
    if value is None:
        if required:
            raise serializers.ValidationError(f'{label} est obligatoire.')
        return value
    value = clean_text(value)
    if not value:
        if required:
            raise serializers.ValidationError(f'{label} est obligatoire.')
        return ''
    if len(value) < min_length:
        raise serializers.ValidationError(f'{label} doit contenir au moins {min_length} caractères.')
    if max_length is not None and len(value) > max_length:
        raise serializers.ValidationError(f'{label} ne doit pas dépasser {max_length} caractères.')
    if '<' in value or '>' in value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise serializers.ValidationError(f'{label} contient des caractères interdits.')
    return value


def validate_name(value, label, *, required=True, min_length=3, max_length=120):
    value = validate_text(value, label, required=required, min_length=min_length, max_length=max_length)
    if value and not NAME_PATTERN.fullmatch(value):
        raise serializers.ValidationError(f'{label} doit commencer par une lettre et contenir uniquement des lettres, espaces, apostrophes ou tirets.')
    return value


def validate_phone(value, *, required=False):
    value = clean_text(value or '').replace(' ', '').replace('.', '').replace('-', '')
    if value.startswith('+221'):
        value = value[4:]
    if not value:
        if required:
            raise serializers.ValidationError('Le numéro de téléphone est obligatoire.')
        return ''
    if not PHONE_PATTERN.fullmatch(value):
        raise serializers.ValidationError('Veuillez saisir un numéro sénégalais valide à 9 chiffres.')
    return value


def validate_gps(value):
    value = clean_text(value or '')
    if not value:
        return ''
    match = GPS_PATTERN.fullmatch(value)
    if not match or not (-90 <= float(match.group(1)) <= 90) or not (-180 <= float(match.group(2)) <= 180):
        raise serializers.ValidationError('Les coordonnées GPS doivent être au format latitude, longitude valide.')
    return value


def validate_date_order(attrs, start_key, end_key, message):
    start = attrs.get(start_key)
    end = attrs.get(end_key)
    if start and end and end < start:
        raise serializers.ValidationError({end_key: message})


def reject_future(value, label):
    if value and value > date.today():
        raise serializers.ValidationError(f'{label} ne peut pas être dans le futur.')
    return value


def validate_non_negative(value, label, *, strictly_positive=False):
    if value is None:
        return value
    value = Decimal(value)
    if strictly_positive and value <= 0:
        raise serializers.ValidationError(f'{label} doit être supérieur à zéro.')
    if not strictly_positive and value < 0:
        raise serializers.ValidationError(f'{label} ne peut pas être négatif.')
    return value
