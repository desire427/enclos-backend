from django.contrib import admin
from .models import Alimentation, TypeAliment, FrequenceAlimentation


@admin.register(TypeAliment)
class TypeAlimentAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'description')
    search_fields = ('nom',)


@admin.register(FrequenceAlimentation)
class FrequenceAlimentationAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'description')
    search_fields = ('nom',)


@admin.register(Alimentation)
class AlimentationAdmin(admin.ModelAdmin):
    list_display  = ('animal', 'ferme', 'type_aliment', 'quantite_kg', 'frequence', 'date_alimentation')
    search_fields = ('type_aliment__nom', 'frequence__nom')
    list_filter   = ('ferme', 'date_alimentation', 'type_aliment', 'frequence')
    readonly_fields = ('date_creation', 'date_modification')
