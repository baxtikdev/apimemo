from __future__ import annotations

from typing import Any

from apimemo.buffer import LogBuffer
from apimemo.types import RequestLog


def dispatch_async_flush(coro_fn: Any, entries: list[RequestLog]) -> None:
    """Run an async flush function from a sync context (background thread).

    If an event loop is running (e.g. inside an async framework), schedules
    the coroutine on that loop and waits. Otherwise, creates a new loop.
    """
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
            pass  # async flush already logs errors
    else:
        asyncio.run(coro_fn(entries))


class BaseIntegration:
    """Base class for all database integrations.

    Provides shared LogBuffer management, httpx client/transport factories,
    and requests.Session factory. Subclasses only need to implement _flush().
    """

    def __init__(self) -> None:
        self._buffer = LogBuffer(self._flush)
        self._buffer.start()

    def _flush(self, entries: list[RequestLog]) -> None:
        raise NotImplementedError

    def get_transport(self) -> Any:
        """Get a sync httpx transport that logs requests."""
        import httpx

        from apimemo.interceptors.httpx_transport import ApimemoTransport

        return ApimemoTransport(self._buffer, base_transport=httpx.HTTPTransport())

    def get_async_transport(self) -> Any:
        """Get an async httpx transport that logs requests."""
        import httpx

        from apimemo.interceptors.httpx_transport import AsyncApimemoTransport

        return AsyncApimemoTransport(self._buffer, base_transport=httpx.AsyncHTTPTransport())

    def get_client(self, **kwargs: Any) -> Any:
        """Get a sync httpx.Client that logs requests."""
        import httpx

        return httpx.Client(transport=self.get_transport(), **kwargs)

    def get_async_client(self, **kwargs: Any) -> Any:
        """Get an async httpx.AsyncClient that logs requests."""
        import httpx

        return httpx.AsyncClient(transport=self.get_async_transport(), **kwargs)

    def get_session(self, **kwargs: Any) -> Any:
        """Get a requests.Session that logs requests."""
        from apimemo.interceptors.requests_session import ApimemoSession

        return ApimemoSession(self._buffer, **kwargs)

    def stop(self) -> None:
        """Stop the buffer and flush remaining entries."""
        self._buffer.stop()
