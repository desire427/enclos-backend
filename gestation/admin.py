from django.contrib import admin
from .models import Gestation


@admin.register(Gestation)
class GestationAdmin(admin.ModelAdmin):
    list_display = ('animal', 'ferme', 'date_debut', 'date_prevue', 'duree_jours', 'statut')
    search_fields = ('statut', 'note')
    list_filter = ('ferme', 'statut')
