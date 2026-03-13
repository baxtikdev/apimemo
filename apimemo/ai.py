from __future__ import annotations

import json
from typing import Any

from apimemo.pricing import calculate_cost
from apimemo.types import RequestLog

_AI_HOSTS = {
    "api.openai.com": "openai",
    "api.anthropic.com": "anthropic",
    "generativelanguage.googleapis.com": "google",
    "api.groq.com": "groq",
    "api.mistral.ai": "mistral",
    "api.cohere.com": "cohere",
    "api.together.xyz": "together",
    "api.fireworks.ai": "fireworks",
    "api.deepseek.com": "deepseek",
    "api.perplexity.ai": "perplexity",
}


def enrich_ai_fields(log: RequestLog) -> None:
    provider = _AI_HOSTS.get(log.host)
    if provider is None:
        return

    log.provider = provider

    body = _parse_json(log.response_body)
    if not body:
        return

    model = body.get("model")
    if model:
        log.ai_model = str(model)

    usage = _extract_usage(body, provider)
    if usage:
        log.input_tokens = usage.get("input", 0)
        log.output_tokens = usage.get("output", 0)
        log.total_tokens = log.input_tokens + log.output_tokens
        cost = calculate_cost(log.ai_model or "", log.input_tokens, log.output_tokens)
        if cost is not None:
            log.cost_usd = cost


def _parse_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_usage(body: dict[str, Any], provider: str) -> dict[str, int] | None:
    usage = body.get("usage")
    if not usage or not isinstance(usage, dict):
        return None

    if provider == "anthropic":
        return {
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
        }

    if provider == "google":
        return {
            "input": usage.get("promptTokenCount", 0),
            "output": usage.get("candidatesTokenCount", 0),
        }

    return {
        "input": usage.get("prompt_tokens", 0),
        "output": usage.get("completion_tokens", 0),
    }
