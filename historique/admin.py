from django.contrib import admin
from .models import HistoriqueEvenement


@admin.register(HistoriqueEvenement)
class HistoriqueEvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'ferme', 'animal', 'type_evenement', 'date_evenement', 'source_ia')
    search_fields = ('titre', 'description')
    list_filter = ('ferme', 'type_evenement', 'source_ia')
