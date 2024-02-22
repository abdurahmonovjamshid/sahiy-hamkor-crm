from django.apps import AppConfig


class AzamatSehConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Azamat_seh'
    verbose_name = 'Multipack'

    def ready(self):
        import Azamat_seh.views
