from django.apps import AppConfig


class AnvarakaSkladConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Anvaraka_sklad'

    def ready(self):
        import Anvaraka_sklad.views
