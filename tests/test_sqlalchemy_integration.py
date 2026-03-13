from __future__ import annotations

from apimemo.integrations.sqlalchemy import ApiLogMixin, SqlAlchemyIntegration


class TestApiLogMixin:
    def test_has_required_columns(self) -> None:
        required = [
            "id", "method", "url", "host", "path", "status_code",
            "request_headers", "request_body", "response_headers", "response_body",
            "duration_ms", "error", "created_at",
        ]
        for col_name in required:
            assert hasattr(ApiLogMixin, col_name), f"Missing column: {col_name}"


class TestSqlAlchemyIntegration:
    def test_creates_integration(self) -> None:
        from unittest.mock import MagicMock

        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        integration = SqlAlchemyIntegration(mock_engine, session_factory=mock_session_factory)
        assert integration is not None
        integration.stop()

    def test_get_client_returns_httpx(self) -> None:
        from unittest.mock import MagicMock

        import httpx

        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        integration = SqlAlchemyIntegration(mock_engine, session_factory=mock_session_factory)

        client = integration.get_client()
        assert isinstance(client, httpx.Client)
        client.close()
        integration.stop()

    def test_get_async_client_returns_httpx(self) -> None:
        from unittest.mock import MagicMock

        import httpx

        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        integration = SqlAlchemyIntegration(mock_engine, session_factory=mock_session_factory)

        client = integration.get_async_client()
        assert isinstance(client, httpx.AsyncClient)
        integration.stop()

    def test_get_session_returns_requests_session(self) -> None:
        from unittest.mock import MagicMock

        from apimemo.interceptors.requests_session import ApimemoSession

        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        integration = SqlAlchemyIntegration(mock_engine, session_factory=mock_session_factory)

        session = integration.get_session()
        assert isinstance(session, ApimemoSession)
        integration.stop()
