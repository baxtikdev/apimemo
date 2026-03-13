from __future__ import annotations

import atexit
import logging
import threading
from typing import Callable

from apimemo.config import get_config
from apimemo.types import RequestLog

logger = logging.getLogger("apimemo")


class LogBuffer:
    def __init__(self, flush_fn: Callable[[list[RequestLog]], None]):
        self._flush_fn = flush_fn
        self._buffer: list[RequestLog] = []
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._schedule_flush()
        atexit.register(self.flush)

    def add(self, entry: RequestLog) -> None:
        config = get_config()
        if not config.enabled:
            return

        entry.truncate(config.max_body_size)

        should_flush = False
        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) >= config.batch_size:
                should_flush = True

        if should_flush:
            self.flush()

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            entries = self._buffer.copy()
            self._buffer.clear()

        try:
            self._flush_fn(entries)
        except Exception:
            logger.exception("apimemo: flush failed, %d entries lost", len(entries))

    def _schedule_flush(self) -> None:
        config = get_config()
        self._timer = threading.Timer(config.flush_interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        self.flush()
        if self._started:
            self._schedule_flush()

    def stop(self) -> None:
        self._started = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self.flush()
