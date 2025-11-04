# src/adapters/process_probe.py
from __future__ import annotations

import os
from typing import Optional
from ..core.ports import ProcessProbePort


class SimpleProcessProbe(ProcessProbePort):
    """
    Cross-platform liveness check using os.kill(pid, 0).

    Notes:
        - On POSIX, signal 0 probes for existence.
        - On Windows (Py3.8+), os.kill exists and signal 0 is also supported.
        - This is best-effort; zombie or permission edge cases may occur.
    """

    def is_alive(self, pid: Optional[int]) -> bool:
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False
