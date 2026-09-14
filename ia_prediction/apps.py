from django.apps import AppConfig


class IaPredictionConfig(AppConfig):
    name = 'ia_prediction'
    verbose_name = 'IA Prédiction'

    def ready(self):
        import ia_prediction.signals  # noqa: F401
