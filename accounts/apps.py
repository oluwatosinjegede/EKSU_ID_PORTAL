from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "User & Access Management"

    def ready(self):
        """
        Safe startup hook.

        Import signals here ONLY if you actually create:
        accounts/signals.py

        Wrapped in try/except to prevent startup crash
        during migrations or partial deploys.
        """
        try:
            import accounts.signals  # noqa: F401
        except Exception:
            # No signals yet — safe to ignore
            pass
