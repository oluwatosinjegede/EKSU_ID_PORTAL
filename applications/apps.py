from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "applications"

    def ready(self):
        # Import signals safely (no side effects, no circular import)
        try:
            import applications.signals  # noqa
        except Exception as e:
            print("APPLICATIONS SIGNAL LOAD ERROR:", e)
