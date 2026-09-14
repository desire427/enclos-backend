from django.contrib import admin

from .models import Ferme


@admin.register(Ferme)
class FermeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'localisation', 'superficie', 'proprietaire', 'date_creation')
    search_fields = ('nom', 'localisation', 'proprietaire__username')
    list_filter = ('date_creation',)
