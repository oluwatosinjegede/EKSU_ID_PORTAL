from django.apps import AppConfig


class IdcardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "idcards"

    def ready(self):
        # Import signals safely (no circular import)
        import idcards.signals  # noqa
