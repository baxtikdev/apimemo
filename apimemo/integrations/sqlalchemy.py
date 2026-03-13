from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

try:
    from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Uuid
except ImportError:
    raise ImportError("Install apimemo[sqlalchemy]: pip install apimemo[sqlalchemy]") from None

from apimemo.integrations._base import BaseIntegration, dispatch_async_flush
from apimemo.types import RequestLog

logger = logging.getLogger("apimemo")


class ApiLogMixin:
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    method = Column(String(10), nullable=False, index=True)
    url = Column(Text, nullable=False)
    host = Column(String(255), nullable=False, index=True)
    path = Column(String(2048), nullable=False)
    status_code = Column(Integer, nullable=False, index=True)
    request_headers = Column(Text, nullable=True)
    request_body = Column(Text, nullable=True)
    response_headers = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=False, default=0.0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class SqlAlchemyIntegration(BaseIntegration):
    def __init__(self, engine: Any, session_factory: Any = None):
        self._engine = engine
        self._session_factory = session_factory

        if session_factory is None:
            from sqlalchemy.ext.asyncio import async_sessionmaker

            self._session_factory = async_sessionmaker(engine, expire_on_commit=False)

        super().__init__()

    def _flush(self, entries: list[RequestLog]) -> None:
        dispatch_async_flush(self._async_flush, entries)

    async def _async_flush(self, entries: list[RequestLog]) -> None:
        from sqlalchemy import text

        try:
            async with self._session_factory() as session:
                for entry in entries:
                    await session.execute(
                        text(
                            "INSERT INTO api_logs "
                            "(id, method, url, host, path, status_code, request_headers, request_body, "
                            "response_headers, response_body, duration_ms, error, created_at) "
                            "VALUES (:id, :method, :url, :host, :path, :status_code, :req_h, :req_b, "
                            ":res_h, :res_b, :duration_ms, :error, :created_at)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "method": entry.method,
                            "url": entry.url,
                            "host": entry.host,
                            "path": entry.path,
                            "status_code": entry.status_code,
                            "req_h": json.dumps(entry.request_headers) if entry.request_headers else None,
                            "req_b": entry.request_body,
                            "res_h": json.dumps(entry.response_headers) if entry.response_headers else None,
                            "res_b": entry.response_body,
                            "duration_ms": entry.duration_ms,
                            "error": entry.error,
                            "created_at": entry.created_at,
                        },
                    )
                await session.commit()
        except Exception:
            logger.exception("apimemo: failed to flush %d entries", len(entries))

    def mount_admin(self, app: Any, model: Any = None) -> None:
        try:
            from apimemo.integrations._fastapi_admin import mount_admin

            mount_admin(app, self._engine, model=model)
        except ImportError:
            raise ImportError("Install apimemo[fastapi-admin]: pip install apimemo[fastapi-admin]") from None
