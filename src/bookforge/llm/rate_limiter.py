from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time

@dataclass
class RateLimiter:
    requests_per_minute: int

    def __post_init__(self) -> None:
        self._timestamps = deque()
        self._lock = threading.Lock()

    def wait(self) -> None:
        if self.requests_per_minute <= 0:
            return
        window = 60.0
        while True:
            with self._lock:
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] >= window:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.requests_per_minute:
                    self._timestamps.append(now)
                    return

                earliest = self._timestamps[0]
                sleep_for = max(0.0, window - (now - earliest))
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                # If the window advanced while unlocked, re-check immediately.
                continue
