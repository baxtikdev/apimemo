from __future__ import annotations

import fnmatch
import threading
from dataclasses import asdict, dataclass

_lock = threading.Lock()
_config: ApiMemoConfig | None = None

_SENTINEL = object()


@dataclass(frozen=True)
class ApiMemoConfig:
    enabled: bool = True
    max_body_size: int = 10240  # 10KB — truncate request/response body
    ttl_days: int = 30  # auto-delete logs older than N days, 0 = never
    batch_size: int = 50  # flush after N logs
    flush_interval: float = 5.0  # flush every N seconds
    ignore_hosts: tuple[str, ...] = ()  # fnmatch patterns: ("localhost", "*.internal.io")
    ignore_paths: tuple[str, ...] = ()  # fnmatch patterns: ("/health", "/metrics")
    log_request_body: bool = True
    log_response_body: bool = True
    log_headers: bool = False  # headers may contain secrets

    def should_ignore(self, host: str, path: str) -> bool:
        for pattern in self.ignore_hosts:
            if fnmatch.fnmatch(host, pattern):
                return True
        for pattern in self.ignore_paths:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False


def configure(
    enabled: object = _SENTINEL,
    max_body_size: object = _SENTINEL,
    ttl_days: object = _SENTINEL,
    batch_size: object = _SENTINEL,
    flush_interval: object = _SENTINEL,
    ignore_hosts: tuple[str, ...] | list[str] | object = _SENTINEL,
    ignore_paths: tuple[str, ...] | list[str] | object = _SENTINEL,
    log_request_body: object = _SENTINEL,
    log_response_body: object = _SENTINEL,
    log_headers: object = _SENTINEL,
) -> ApiMemoConfig:
    """Update configuration. Only provided fields are changed; others are preserved.

    Call with no arguments to reset to defaults.
    """
    global _config

    with _lock:
        current = _config or ApiMemoConfig()

    # No arguments → reset to defaults
    all_sentinel = all(
        v is _SENTINEL
        for v in (
            enabled, max_body_size, ttl_days, batch_size, flush_interval,
            ignore_hosts, ignore_paths, log_request_body, log_response_body, log_headers,
        )
    )
    if all_sentinel:
        config = ApiMemoConfig()
    else:
        # Merge: start from current config, override only provided fields
        values = asdict(current)
        if enabled is not _SENTINEL:
            values["enabled"] = enabled
        if max_body_size is not _SENTINEL:
            values["max_body_size"] = max_body_size
        if ttl_days is not _SENTINEL:
            values["ttl_days"] = ttl_days
        if batch_size is not _SENTINEL:
            values["batch_size"] = batch_size
        if flush_interval is not _SENTINEL:
            values["flush_interval"] = flush_interval
        if ignore_hosts is not _SENTINEL:
            values["ignore_hosts"] = tuple(ignore_hosts)  # type: ignore[arg-type]
        if ignore_paths is not _SENTINEL:
            values["ignore_paths"] = tuple(ignore_paths)  # type: ignore[arg-type]
        if log_request_body is not _SENTINEL:
            values["log_request_body"] = log_request_body
        if log_response_body is not _SENTINEL:
            values["log_response_body"] = log_response_body
        if log_headers is not _SENTINEL:
            values["log_headers"] = log_headers
        config = ApiMemoConfig(**values)

    with _lock:
        _config = config

    return config


def get_config() -> ApiMemoConfig:
    global _config
    with _lock:
        if _config is None:
            _config = ApiMemoConfig()
        return _config
