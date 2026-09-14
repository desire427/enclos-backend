from django.apps import AppConfig


class HistoriqueConfig(AppConfig):
    name = 'historique'

    def ready(self):
        # Enregistre les signals automatiquement au démarrage de l'app
        import historique.signals  # noqa: F401
