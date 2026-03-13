from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    raise ImportError("Install apimemo[httpx]: pip install apimemo[httpx]") from None

from apimemo.ai import enrich_ai_fields
from apimemo.config import get_config
from apimemo.types import RequestLog

if TYPE_CHECKING:
    from apimemo.buffer import LogBuffer


def _extract_body(content: bytes | None, max_size: int) -> str | None:
    if not content:
        return None
    try:
        text = content.decode("utf-8", errors="replace")
        if len(text) > max_size:
            return text[:max_size] + "...(truncated)"
        return text
    except Exception:
        return None


def _extract_headers(headers: Any) -> dict[str, str]:
    return dict(headers) if headers else {}


def _build_log(
    request: httpx.Request,
    response: httpx.Response | None,
    duration_ms: float,
    error: str | None = None,
) -> RequestLog | None:
    config = get_config()
    parsed = urlparse(str(request.url))
    host = parsed.hostname or ""
    path = parsed.path or "/"

    if config.should_ignore(host, path):
        return None

    log = RequestLog(
        method=request.method,
        url=str(request.url),
        host=host,
        path=path,
        status_code=response.status_code if response else 0,
        duration_ms=duration_ms,
        error=error,
    )

    if config.log_request_body:
        log.request_body = _extract_body(request.content, config.max_body_size)
    if config.log_headers:
        log.request_headers = _extract_headers(request.headers)

    if response:
        if config.log_response_body:
            log.response_body = _extract_body(response.content, config.max_body_size)
        if config.log_headers:
            log.response_headers = _extract_headers(response.headers)

    enrich_ai_fields(log)

    return log


class ApimemoTransport(httpx.BaseTransport):
    def __init__(self, buffer: LogBuffer, base_transport: httpx.BaseTransport | None = None):
        self._buffer = buffer
        self._transport = base_transport or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        start = time.perf_counter()
        response = None
        error = None
        try:
            response = self._transport.handle_request(request)
            return response
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            if response:
                response.read()
            log = _build_log(request, response, duration_ms, error)
            if log:
                self._buffer.add(log)


class AsyncApimemoTransport(httpx.AsyncBaseTransport):
    def __init__(self, buffer: LogBuffer, base_transport: httpx.AsyncBaseTransport | None = None):
        self._buffer = buffer
        self._transport = base_transport or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        start = time.perf_counter()
        response = None
        error = None
        try:
            response = await self._transport.handle_async_request(request)
            return response
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            if response:
                await response.aread()
            log = _build_log(request, response, duration_ms, error)
            if log:
                self._buffer.add(log)
