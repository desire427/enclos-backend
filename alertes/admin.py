from django.contrib import admin
from .models import Alerte


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ('type_alerte', 'ferme', 'animal', 'statut', 'date_creation')
    search_fields = ('type_alerte', 'message')
    list_filter = ('ferme', 'type_alerte', 'statut')
