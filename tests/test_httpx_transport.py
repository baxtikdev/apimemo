from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from apimemo.buffer import LogBuffer
from apimemo.config import configure
from apimemo.interceptors.httpx_transport import ApimemoTransport, AsyncApimemoTransport
from apimemo.types import RequestLog


def _mock_buffer() -> LogBuffer:
    buf = MagicMock(spec=LogBuffer)
    buf.add = MagicMock()
    return buf


class TestApimemoTransport:
    def setup_method(self) -> None:
        configure()

    def test_logs_request(self) -> None:
        mock_response = httpx.Response(200, content=b'{"ok": true}')
        mock_response._content = b'{"ok": true}'

        inner = MagicMock()
        inner.handle_request.return_value = mock_response

        buf = _mock_buffer()
        transport = ApimemoTransport(buf, base_transport=inner)

        request = httpx.Request("GET", "https://api.example.com/users")
        response = transport.handle_request(request)

        assert response.status_code == 200
        buf.add.assert_called_once()
        log: RequestLog = buf.add.call_args[0][0]
        assert log.method == "GET"
        assert log.host == "api.example.com"
        assert log.path == "/users"
        assert log.status_code == 200

    def test_logs_error(self) -> None:
        inner = MagicMock()
        inner.handle_request.side_effect = httpx.ConnectError("refused")

        buf = _mock_buffer()
        transport = ApimemoTransport(buf, base_transport=inner)

        request = httpx.Request("POST", "https://api.example.com/fail")
        with pytest.raises(httpx.ConnectError):
            transport.handle_request(request)

        buf.add.assert_called_once()
        log: RequestLog = buf.add.call_args[0][0]
        assert log.status_code == 0
        assert "ConnectError" in log.error

    def test_ignores_matching_host(self) -> None:
        configure(ignore_hosts=("api.example.com",))

        mock_response = httpx.Response(200, content=b"ok")
        mock_response._content = b"ok"

        inner = MagicMock()
        inner.handle_request.return_value = mock_response

        buf = _mock_buffer()
        transport = ApimemoTransport(buf, base_transport=inner)

        request = httpx.Request("GET", "https://api.example.com/users")
        transport.handle_request(request)

        buf.add.assert_not_called()

    def teardown_method(self) -> None:
        configure()


class TestAsyncApimemoTransport:
    def setup_method(self) -> None:
        configure()

    @pytest.mark.asyncio
    async def test_logs_request(self) -> None:
        mock_response = httpx.Response(201, content=b'{"created": true}')
        mock_response._content = b'{"created": true}'

        inner = MagicMock()

        async def mock_handle(req: httpx.Request) -> httpx.Response:
            return mock_response

        inner.handle_async_request = mock_handle

        buf = _mock_buffer()
        transport = AsyncApimemoTransport(buf, base_transport=inner)

        request = httpx.Request("POST", "https://api.example.com/create")
        response = await transport.handle_async_request(request)

        assert response.status_code == 201
        buf.add.assert_called_once()
        log: RequestLog = buf.add.call_args[0][0]
        assert log.method == "POST"
        assert log.status_code == 201

    @pytest.mark.asyncio
    async def test_logs_error(self) -> None:
        inner = MagicMock()

        async def mock_handle(req: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out")

        inner.handle_async_request = mock_handle

        buf = _mock_buffer()
        transport = AsyncApimemoTransport(buf, base_transport=inner)

        request = httpx.Request("GET", "https://api.example.com/slow")
        with pytest.raises(httpx.TimeoutException):
            await transport.handle_async_request(request)

        buf.add.assert_called_once()
        log: RequestLog = buf.add.call_args[0][0]
        assert log.status_code == 0
        assert "TimeoutException" in log.error

    def teardown_method(self) -> None:
        configure()
