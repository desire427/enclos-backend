from django.contrib import admin
from .models import PredictionResultat


@admin.register(PredictionResultat)
class PredictionResultatAdmin(admin.ModelAdmin):
    list_display  = ('animal', 'est_malade', 'probabilite_pct', 'declencheur', 'envoye_n8n', 'date_prediction')
    list_filter   = ('est_malade', 'declencheur', 'envoye_n8n')
    readonly_fields = ('animal', 'declencheur', 'est_malade', 'probabilite',
                       'shap_values', 'features_used', 'explication_llm',
                       'comparaison_historique', 'envoye_n8n', 'date_prediction')
    ordering      = ('-date_prediction',)

    @admin.display(description='Probabilité', ordering='probabilite')
    def probabilite_pct(self, obj):
        return f'{obj.probabilite:.0%}'
