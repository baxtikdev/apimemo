try:
    from django.apps import AppConfig
except ImportError:
    # Not a Django project — apps.py is only loaded by Django's app registry.
    # Provide a placeholder so the module can be imported without error.
    AppConfig = None  # type: ignore[assignment,misc]


if AppConfig is not None:

    class ApimemoConfig(AppConfig):  # type: ignore[misc]
        name = "apimemo"
        verbose_name = "API Memo"
        default_auto_field = "django.db.models.BigAutoField"
