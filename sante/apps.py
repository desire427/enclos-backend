from django.apps import AppConfig


class SanteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sante'

    def ready(self):
        from . import signals  # noqa: F401
