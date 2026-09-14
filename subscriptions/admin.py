from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'date_debut', 'date_fin', 'statut', 'montant_paye', 'date_paiement')
    list_filter = ('statut',)
