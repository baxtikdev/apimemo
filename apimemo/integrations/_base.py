from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from apimemo.buffer import LogBuffer
from apimemo.types import RequestLog

logger = logging.getLogger("apimemo")


def dispatch_async_flush(coro_fn: Any, entries: list[RequestLog]) -> None:
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro_fn(entries), loop)
        try:
            future.result(timeout=10)
        except Exception:
            logger.exception("apimemo: async flush failed, %d entries lost", len(entries))
    else:
        asyncio.run(coro_fn(entries))


class BaseIntegration(ABC):
    def __init__(self) -> None:
        self._buffer = LogBuffer(self._flush)
        self._buffer.start()

    @abstractmethod
    def _flush(self, entries: list[RequestLog]) -> None: ...

    def get_transport(self) -> Any:
        import httpx

        from apimemo.interceptors.httpx_transport import ApimemoTransport

        return ApimemoTransport(self._buffer, base_transport=httpx.HTTPTransport())

    def get_async_transport(self) -> Any:
        import httpx

        from apimemo.interceptors.httpx_transport import AsyncApimemoTransport

        return AsyncApimemoTransport(self._buffer, base_transport=httpx.AsyncHTTPTransport())

    def get_client(self, **kwargs: Any) -> Any:
        import httpx

        return httpx.Client(transport=self.get_transport(), **kwargs)

    def get_async_client(self, **kwargs: Any) -> Any:
        import httpx

        return httpx.AsyncClient(transport=self.get_async_transport(), **kwargs)

    def get_session(self, **kwargs: Any) -> Any:
        from apimemo.interceptors.requests_session import ApimemoSession

        return ApimemoSession(self._buffer, **kwargs)

    def stop(self) -> None:
        self._buffer.stop()
