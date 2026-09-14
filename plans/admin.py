from django.contrib import admin

from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'duree_mois', 'nb_fermes_max', 'nb_animaux_max', 'acces_ia', 'acces_support', 'acces_analyses')
    list_filter = ('acces_ia', 'acces_support', 'acces_analyses')
