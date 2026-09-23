from django.apps import AppConfig


class AlertesConfig(AppConfig):
    name = 'alertes'

    def ready(self):
        from . import signals  # noqa: F401
