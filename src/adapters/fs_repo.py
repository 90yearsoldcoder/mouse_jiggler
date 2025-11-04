# src/adapters/fs_repo.py
from __future__ import annotations

import os
from typing import Optional
from ..core.ports import StateRepoPort


class FilesystemStateRepo(StateRepoPort):
    """
    File-based state repository for PID and STOP flag.

    Layout:
        state_dir/
          ├─ jiggler.pid
          └─ STOP
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self._state_dir = os.path.abspath(os.path.expanduser(base_dir))
        else:
            if os.name == "nt":
                root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
                self._state_dir = os.path.join(root, "MouseJiggler")
            else:
                self._state_dir = os.path.join(os.path.expanduser("~"), ".mousejiggler")
        os.makedirs(self._state_dir, exist_ok=True)

        self._pid_path = os.path.join(self._state_dir, "jiggler.pid")
        self._stop_path = os.path.join(self._state_dir, "STOP")

    def state_dir(self) -> str:
        return self._state_dir

    def read_pid(self) -> Optional[int]:
        try:
            with open(self._pid_path, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception:
            return None

    def write_pid(self, pid: int) -> None:
        with open(self._pid_path, "w", encoding="utf-8") as f:
            f.write(str(pid))

    def clear_pid(self) -> None:
        try:
            os.remove(self._pid_path)
        except FileNotFoundError:
            pass

    def has_stop(self) -> bool:
        return os.path.exists(self._stop_path)

    def set_stop(self) -> None:
        # Create/Touch STOP flag
        with open(self._stop_path, "w", encoding="utf-8"):
            pass

    def clear_stop(self) -> None:
        try:
            os.remove(self._stop_path)
        except FileNotFoundError:
            pass
