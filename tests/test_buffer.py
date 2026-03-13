from __future__ import annotations

import threading
import time

from apimemo.buffer import LogBuffer
from apimemo.config import configure
from apimemo.types import RequestLog


def _make_log(**kwargs) -> RequestLog:
    defaults = dict(method="GET", url="https://example.com", host="example.com", path="/", status_code=200)
    defaults.update(kwargs)
    return RequestLog(**defaults)


class TestLogBuffer:
    def setup_method(self) -> None:
        configure(batch_size=5, flush_interval=60.0)  # large interval — manual flush

    def test_flush_on_batch_size(self) -> None:
        flushed: list[list[RequestLog]] = []
        buf = LogBuffer(lambda entries: flushed.append(entries))
        buf.start()

        for _ in range(5):
            buf.add(_make_log())

        assert len(flushed) == 1
        assert len(flushed[0]) == 5
        buf.stop()

    def test_flush_on_stop(self) -> None:
        flushed: list[list[RequestLog]] = []
        buf = LogBuffer(lambda entries: flushed.append(entries))
        buf.start()

        buf.add(_make_log())
        buf.add(_make_log())
        assert len(flushed) == 0  # not enough for batch

        buf.stop()
        assert len(flushed) == 1
        assert len(flushed[0]) == 2

    def test_flush_on_timer(self) -> None:
        configure(batch_size=1000, flush_interval=0.1)
        flushed: list[list[RequestLog]] = []
        buf = LogBuffer(lambda entries: flushed.append(entries))
        buf.start()

        buf.add(_make_log())
        time.sleep(0.3)

        assert len(flushed) >= 1
        buf.stop()

    def test_disabled_config(self) -> None:
        configure(enabled=False)
        flushed: list[list[RequestLog]] = []
        buf = LogBuffer(lambda entries: flushed.append(entries))
        buf.start()

        for _ in range(10):
            buf.add(_make_log())

        buf.stop()
        assert len(flushed) == 0

    def test_thread_safety(self) -> None:
        configure(batch_size=100, flush_interval=60.0)
        flushed: list[list[RequestLog]] = []
        lock = threading.Lock()

        def safe_flush(entries: list[RequestLog]) -> None:
            with lock:
                flushed.append(entries)

        buf = LogBuffer(safe_flush)
        buf.start()

        def worker() -> None:
            for _ in range(50):
                buf.add(_make_log())

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        buf.stop()

        total = sum(len(batch) for batch in flushed)
        assert total == 200

    def test_flush_error_does_not_crash(self) -> None:
        def bad_flush(entries: list[RequestLog]) -> None:
            raise RuntimeError("DB down")

        buf = LogBuffer(bad_flush)
        buf.start()

        configure(batch_size=1)
        buf.add(_make_log())  # should not raise
        buf.stop()

    def teardown_method(self) -> None:
        configure()  # reset
