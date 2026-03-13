try:
    from django.apps import AppConfig
except ImportError:
    AppConfig = None  # type: ignore[assignment,misc]


if AppConfig is not None:

    class ApimemoConfig(AppConfig):  # type: ignore[misc]
        name = "apimemo"
        verbose_name = "API Memo"
        default_auto_field = "django.db.models.BigAutoField"
