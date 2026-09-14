from django.contrib import admin
from .models import Animal, Race


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'espece')
    list_filter   = ('espece',)
    search_fields = ('nom',)
    ordering      = ('espece', 'nom')


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display  = ('numero_identification', 'nom', 'espece', 'race', 'sexe', 'presence', 'etat_sante', 'ferme')
    search_fields = ('numero_identification', 'nom')
    list_filter   = ('espece', 'sexe', 'presence', 'etat_sante', 'ferme')
    readonly_fields = ('numero_identification', 'date_creation', 'date_modification')
    ordering      = ('espece', 'numero_identification')
