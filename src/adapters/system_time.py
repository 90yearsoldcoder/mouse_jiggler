# src/adapters/system_time.py
from __future__ import annotations

import time
from ..core.ports import TimePort


class SystemTime(TimePort):
    """
    Production clock based on the standard library 'time' module.
    """

    def now(self) -> float:
        return time.time()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)
