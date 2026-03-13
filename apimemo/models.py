from __future__ import annotations

import uuid

try:
    from django.db import models
except ImportError:
    pass
else:

    class ApiLog(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        method = models.CharField(max_length=10, db_index=True)
        url = models.TextField()
        host = models.CharField(max_length=255, db_index=True)
        path = models.CharField(max_length=2048)
        status_code = models.IntegerField(db_index=True)
        request_headers = models.TextField(blank=True, null=True)
        request_body = models.TextField(blank=True, null=True)
        response_headers = models.TextField(blank=True, null=True)
        response_body = models.TextField(blank=True, null=True)
        duration_ms = models.FloatField(default=0.0)
        error = models.TextField(blank=True, null=True)
        provider = models.CharField(max_length=50, blank=True, null=True, db_index=True)
        ai_model = models.CharField(max_length=255, blank=True, null=True, db_index=True)
        input_tokens = models.IntegerField(blank=True, null=True)
        output_tokens = models.IntegerField(blank=True, null=True)
        total_tokens = models.IntegerField(blank=True, null=True)
        cost_usd = models.FloatField(blank=True, null=True)
        created_at = models.DateTimeField(auto_now_add=True, db_index=True)

        class Meta:
            db_table = "api_logs"
            ordering = ["-created_at"]
            verbose_name = "API Log"
            verbose_name_plural = "API Logs"

        def __str__(self) -> str:
            return f"{self.method} {self.host}{self.path} [{self.status_code}]"
