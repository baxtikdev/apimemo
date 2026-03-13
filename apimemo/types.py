from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RequestLog:
    method: str
    url: str
    host: str
    path: str
    status_code: int
    request_headers: dict | None = None
    request_body: str | None = None
    response_headers: dict | None = None
    response_body: str | None = None
    duration_ms: float = 0.0
    error: str | None = None
    provider: str | None = None
    ai_model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def truncate(self, max_size: int) -> None:
        if self.request_body and len(self.request_body) > max_size:
            self.request_body = self.request_body[:max_size] + "...(truncated)"
        if self.response_body and len(self.response_body) > max_size:
            self.response_body = self.response_body[:max_size] + "...(truncated)"
