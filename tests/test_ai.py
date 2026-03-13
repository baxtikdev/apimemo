from __future__ import annotations

import json

from apimemo.ai import enrich_ai_fields
from apimemo.types import RequestLog


def _make_log(host: str, response_body: str | None = None) -> RequestLog:
    return RequestLog(
        method="POST",
        url=f"https://{host}/v1/chat/completions",
        host=host,
        path="/v1/chat/completions",
        status_code=200,
        response_body=response_body,
    )


class TestEnrichAiFields:
    def test_non_ai_host_skipped(self) -> None:
        log = _make_log("api.example.com")
        enrich_ai_fields(log)
        assert log.provider is None

    def test_openai(self) -> None:
        body = json.dumps(
            {
                "model": "gpt-4o",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            }
        )
        log = _make_log("api.openai.com", body)
        enrich_ai_fields(log)
        assert log.provider == "openai"
        assert log.ai_model == "gpt-4o"
        assert log.input_tokens == 100
        assert log.output_tokens == 50
        assert log.total_tokens == 150
        assert log.cost_usd is not None

    def test_anthropic(self) -> None:
        body = json.dumps(
            {
                "model": "claude-3-5-sonnet-20241022",
                "usage": {"input_tokens": 200, "output_tokens": 80},
            }
        )
        log = _make_log("api.anthropic.com", body)
        enrich_ai_fields(log)
        assert log.provider == "anthropic"
        assert log.ai_model == "claude-3-5-sonnet-20241022"
        assert log.input_tokens == 200
        assert log.output_tokens == 80
        assert log.total_tokens == 280

    def test_google(self) -> None:
        body = json.dumps(
            {
                "model": "gemini-2.0-flash",
                "usage": {"promptTokenCount": 50, "candidatesTokenCount": 30},
            }
        )
        log = _make_log("generativelanguage.googleapis.com", body)
        enrich_ai_fields(log)
        assert log.provider == "google"
        assert log.input_tokens == 50
        assert log.output_tokens == 30

    def test_groq(self) -> None:
        body = json.dumps(
            {
                "model": "llama-3.1-70b-versatile",
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            }
        )
        log = _make_log("api.groq.com", body)
        enrich_ai_fields(log)
        assert log.provider == "groq"
        assert log.input_tokens == 10
        assert log.output_tokens == 20

    def test_no_response_body(self) -> None:
        log = _make_log("api.openai.com", None)
        enrich_ai_fields(log)
        assert log.provider == "openai"
        assert log.ai_model is None
        assert log.input_tokens is None

    def test_invalid_json(self) -> None:
        log = _make_log("api.openai.com", "not json")
        enrich_ai_fields(log)
        assert log.provider == "openai"
        assert log.ai_model is None

    def test_no_usage_key(self) -> None:
        body = json.dumps({"model": "gpt-4o"})
        log = _make_log("api.openai.com", body)
        enrich_ai_fields(log)
        assert log.provider == "openai"
        assert log.ai_model == "gpt-4o"
        assert log.input_tokens is None

    def test_deepseek(self) -> None:
        body = json.dumps(
            {
                "model": "deepseek-chat",
                "usage": {"prompt_tokens": 500, "completion_tokens": 300},
            }
        )
        log = _make_log("api.deepseek.com", body)
        enrich_ai_fields(log)
        assert log.provider == "deepseek"
        assert log.total_tokens == 800

    def test_mistral(self) -> None:
        body = json.dumps(
            {
                "model": "mistral-large-latest",
                "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
            }
        )
        log = _make_log("api.mistral.ai", body)
        enrich_ai_fields(log)
        assert log.provider == "mistral"
        assert log.cost_usd is not None
