from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    raise ImportError("Install apimemo[requests]: pip install apimemo[requests]") from None

from apimemo.config import get_config
from apimemo.types import RequestLog

if TYPE_CHECKING:
    from apimemo.buffer import LogBuffer


class ApimemoSession(requests.Session):
    """Drop-in replacement for requests.Session that logs all requests.

    Usage:
        session = ApimemoSession(buffer)
        session.get("https://api.example.com/users")
    """

    def __init__(self, buffer: LogBuffer, **kwargs: Any):
        super().__init__(**kwargs)
        self._buffer = buffer

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        config = get_config()
        parsed = urlparse(url)
        host = parsed.hostname or ""
        path = parsed.path or "/"

        if config.should_ignore(host, path):
            return super().request(method, url, **kwargs)

        start = time.perf_counter()
        response = None
        error = None

        try:
            response = super().request(method, url, **kwargs)
            return response
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            log = RequestLog(
                method=method.upper(),
                url=url,
                host=host,
                path=path,
                status_code=response.status_code if response else 0,
                duration_ms=duration_ms,
                error=error,
            )

            if config.log_request_body:
                body = kwargs.get("data") or kwargs.get("json")
                if body is not None:
                    log.request_body = str(body)[:config.max_body_size] if body else None

            if config.log_headers and response:
                log.request_headers = dict(response.request.headers)
                log.response_headers = dict(response.headers)

            if config.log_response_body and response:
                try:
                    text = response.text
                    if len(text) > config.max_body_size:
                        text = text[: config.max_body_size] + "...(truncated)"
                    log.response_body = text
                except Exception:
                    pass

            log.truncate(config.max_body_size)
            self._buffer.add(log)
