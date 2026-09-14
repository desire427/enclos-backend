from django.conf import settings
from django.db import models


class Role(models.Model):
    nom = models.CharField(max_length=50, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'

    def __str__(self):
        return self.nom


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile', verbose_name='Utilisateur')
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Téléphone')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles', verbose_name='Rôle')
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name='Date d’inscription')
    derniere_connexion = models.DateTimeField(null=True, blank=True, verbose_name='Dernière connexion')
    actif = models.BooleanField(default=True, verbose_name='Actif')

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        return self.user.get_username()
