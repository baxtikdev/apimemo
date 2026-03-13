from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from apimemo.buffer import LogBuffer
from apimemo.config import configure
from apimemo.types import RequestLog

requests = pytest.importorskip("requests")
from apimemo.interceptors.requests_session import ApimemoSession


def _mock_buffer() -> LogBuffer:
    buf = MagicMock(spec=LogBuffer)
    buf.add = MagicMock()
    return buf


class TestApimemoSession:
    def setup_method(self) -> None:
        configure()

    @patch("requests.Session.request")
    def test_logs_request(self, mock_request: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"ok": true}'
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.request = MagicMock()
        mock_resp.request.headers = {"User-Agent": "test"}
        mock_request.return_value = mock_resp

        buf = _mock_buffer()
        session = ApimemoSession(buf)
        resp = session.request("GET", "https://api.example.com/data")

        assert resp.status_code == 200
        buf.add.assert_called_once()
        log: RequestLog = buf.add.call_args[0][0]
        assert log.method == "GET"
        assert log.host == "api.example.com"
        assert log.path == "/data"

    @patch("requests.Session.request")
    def test_logs_error(self, mock_request: MagicMock) -> None:
        mock_request.side_effect = requests.ConnectionError("refused")

        buf = _mock_buffer()
        session = ApimemoSession(buf)

        with pytest.raises(requests.ConnectionError):
            session.request("POST", "https://api.example.com/fail")

        buf.add.assert_called_once()
        log: RequestLog = buf.add.call_args[0][0]
        assert log.status_code == 0
        assert "ConnectionError" in log.error

    @patch("requests.Session.request")
    def test_ignores_matching_path(self, mock_request: MagicMock) -> None:
        configure(ignore_paths=("/health",))

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_request.return_value = mock_resp

        buf = _mock_buffer()
        session = ApimemoSession(buf)
        session.request("GET", "https://api.example.com/health")

        buf.add.assert_not_called()

    def teardown_method(self) -> None:
        configure()
