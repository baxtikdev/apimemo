from __future__ import annotations

from apimemo.types import RequestLog


class TestRequestLog:
    def test_defaults(self) -> None:
        log = RequestLog(method="GET", url="https://example.com", host="example.com", path="/", status_code=200)
        assert log.request_headers is None
        assert log.request_body is None
        assert log.response_body is None
        assert log.duration_ms == 0.0
        assert log.error is None
        assert log.created_at is not None

    def test_truncate(self) -> None:
        body = "x" * 20000
        log = RequestLog(
            method="POST",
            url="https://example.com",
            host="example.com",
            path="/",
            status_code=200,
            request_body=body,
            response_body=body,
        )
        log.truncate(100)
        assert len(log.request_body) == 100 + len("...(truncated)")
        assert log.request_body.endswith("...(truncated)")
        assert len(log.response_body) == 100 + len("...(truncated)")

    def test_truncate_no_op_when_small(self) -> None:
        log = RequestLog(
            method="GET",
            url="https://example.com",
            host="example.com",
            path="/",
            status_code=200,
            request_body="small",
        )
        log.truncate(10000)
        assert log.request_body == "small"

    def test_truncate_none_body(self) -> None:
        log = RequestLog(method="GET", url="https://example.com", host="example.com", path="/", status_code=200)
        log.truncate(100)  # should not raise
        assert log.request_body is None
