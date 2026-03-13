from __future__ import annotations

import pytest

tortoise = pytest.importorskip("tortoise")

from apimemo.integrations.tortoise import ApiLog, TortoiseIntegration


class TestTortoiseApiLog:
    def test_model_has_required_fields(self) -> None:
        fields = {f for f in ApiLog._meta.fields_map}
        required = {"id", "method", "url", "host", "path", "status_code", "duration_ms", "created_at"}
        assert required.issubset(fields)

    def test_meta_table_name(self) -> None:
        assert ApiLog._meta.db_table == "api_logs"


class TestTortoiseIntegration:
    def test_creates_integration(self) -> None:
        integration = TortoiseIntegration()
        assert integration is not None
        integration.stop()

    def test_get_client_returns_httpx(self) -> None:
        import httpx

        integration = TortoiseIntegration()
        client = integration.get_client()
        assert isinstance(client, httpx.Client)
        client.close()
        integration.stop()

    def test_get_async_client_returns_httpx(self) -> None:
        import httpx

        integration = TortoiseIntegration()
        client = integration.get_async_client()
        assert isinstance(client, httpx.AsyncClient)
        integration.stop()
