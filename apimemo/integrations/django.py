from __future__ import annotations

import json
import logging
import uuid

try:
    from django.db import close_old_connections, connection
except ImportError:
    raise ImportError("Install apimemo[django]: pip install apimemo[django]") from None

from apimemo.integrations._base import BaseIntegration
from apimemo.types import RequestLog

logger = logging.getLogger("apimemo")


class DjangoIntegration(BaseIntegration):
    def _flush(self, entries: list[RequestLog]) -> None:
        try:
            close_old_connections()
            with connection.cursor() as cursor:
                for entry in entries:
                    cursor.execute(
                        "INSERT INTO api_logs "
                        "(id, method, url, host, path, status_code, request_headers, request_body, "
                        "response_headers, response_body, duration_ms, error, created_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        [
                            str(uuid.uuid4()),
                            entry.method,
                            entry.url,
                            entry.host,
                            entry.path,
                            entry.status_code,
                            json.dumps(entry.request_headers) if entry.request_headers else None,
                            entry.request_body,
                            json.dumps(entry.response_headers) if entry.response_headers else None,
                            entry.response_body,
                            entry.duration_ms,
                            entry.error,
                            entry.created_at,
                        ],
                    )
        except Exception:
            logger.exception("apimemo: failed to flush %d entries", len(entries))
        finally:
            close_old_connections()
