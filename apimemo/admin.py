from __future__ import annotations

try:
    from django.contrib import admin
except ImportError:
    pass
else:
    from apimemo.models import ApiLog

    @admin.register(ApiLog)
    class ApiLogAdmin(admin.ModelAdmin):
        list_display = (
            "method",
            "host",
            "path",
            "status_code",
            "duration_ms",
            "provider",
            "ai_model",
            "total_tokens",
            "cost_usd",
            "created_at",
        )
        list_filter = ("method", "status_code", "provider", "ai_model")
        search_fields = ("url", "host", "path", "error", "provider", "ai_model")
        readonly_fields = (
            "id",
            "method",
            "url",
            "host",
            "path",
            "status_code",
            "request_headers",
            "request_body",
            "response_headers",
            "response_body",
            "duration_ms",
            "error",
            "provider",
            "ai_model",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cost_usd",
            "created_at",
        )
        ordering = ("-created_at",)
        list_per_page = 50
        date_hierarchy = "created_at"

        def has_add_permission(self, request: object) -> bool:
            return False

        def has_change_permission(self, request: object, obj: object = None) -> bool:
            return False
