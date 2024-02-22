from django.apps import AppConfig


class AnvarakaSkladConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Anvaraka_sklad'
    verbose_name = 'Sklad'

    def ready(self):
        import Anvaraka_sklad.views
