from django.contrib import admin

from .models import Role, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'telephone', 'role', 'date_inscription', 'derniere_connexion', 'actif')
