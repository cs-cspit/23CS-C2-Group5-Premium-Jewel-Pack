from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # import signals to attach them
        try:
            from . import signals  # noqa: F401
        except Exception:
            # failing to import signals at startup should not break the app
            pass
