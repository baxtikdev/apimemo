from __future__ import annotations

try:
    from django.contrib import admin
except ImportError:
    pass
else:
    from apimemo.models import ApiLog

    @admin.register(ApiLog)
    class ApiLogAdmin(admin.ModelAdmin):
        list_display = ("method", "host", "path", "status_code", "duration_ms", "created_at")
        list_filter = ("method", "status_code")
        search_fields = ("url", "host", "path", "error")
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
            "created_at",
        )
        ordering = ("-created_at",)
        list_per_page = 50
        date_hierarchy = "created_at"

        def has_add_permission(self, request: object) -> bool:
            return False

        def has_change_permission(self, request: object, obj: object = None) -> bool:
            return False
