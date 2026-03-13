from __future__ import annotations

import json
import logging
import uuid

try:
    from tortoise import fields, models
except ImportError:
    raise ImportError("Install apimemo[tortoise]: pip install apimemo[tortoise]") from None

from apimemo.integrations._base import BaseIntegration, dispatch_async_flush
from apimemo.types import RequestLog

logger = logging.getLogger("apimemo")


class ApiLog(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    method = fields.CharField(max_length=10, db_index=True)
    url = fields.TextField()
    host = fields.CharField(max_length=255, db_index=True)
    path = fields.CharField(max_length=2048)
    status_code = fields.IntField(db_index=True)
    request_headers = fields.TextField(null=True)
    request_body = fields.TextField(null=True)
    response_headers = fields.TextField(null=True)
    response_body = fields.TextField(null=True)
    duration_ms = fields.FloatField(default=0.0)
    error = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True, db_index=True)

    class Meta:
        table = "api_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.method} {self.host}{self.path} [{self.status_code}]"


class TortoiseIntegration(BaseIntegration):
    def _flush(self, entries: list[RequestLog]) -> None:
        dispatch_async_flush(self._async_flush, entries)

    async def _async_flush(self, entries: list[RequestLog]) -> None:
        try:
            objects = [
                ApiLog(
                    method=entry.method,
                    url=entry.url,
                    host=entry.host,
                    path=entry.path,
                    status_code=entry.status_code,
                    request_headers=json.dumps(entry.request_headers) if entry.request_headers else None,
                    request_body=entry.request_body,
                    response_headers=json.dumps(entry.response_headers) if entry.response_headers else None,
                    response_body=entry.response_body,
                    duration_ms=entry.duration_ms,
                    error=entry.error,
                    created_at=entry.created_at,
                )
                for entry in entries
            ]
            await ApiLog.bulk_create(objects)
        except Exception:
            logger.exception("apimemo: failed to flush %d entries", len(entries))
