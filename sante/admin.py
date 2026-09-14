from django.contrib import admin
from .models import SuiviSante


@admin.register(SuiviSante)
class SuiviSanteAdmin(admin.ModelAdmin):
    list_display = ('animal', 'ferme', 'date_debut', 'statut', 'poids_kg', 'temperature_celsius', 'frequence_cardiaque')
    search_fields = ('statut', 'note')
    list_filter = ('ferme', 'statut')
