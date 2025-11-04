# src/core/ports.py
from __future__ import annotations

import abc
from typing import Optional, Tuple


class MousePort(abc.ABC):
    """
    Abstraction over system mouse control.

    Implementations:
        - PynputMouseAdapter (cross-platform, user-space)
        - Native adapters (Win32 SendInput / macOS Quartz / X11/Wayland)
    """

    @abc.abstractmethod
    def move(self, dx: int, dy: int) -> None:
        """
        Move the mouse relative to the current position.

        Args:
            dx: Horizontal delta in pixels (positive -> right).
            dy: Vertical delta in pixels (positive -> down).

        Raises:
            Exception: If the OS denies input or adapter fails.
        """
        raise NotImplementedError


class StateRepoPort(abc.ABC):
    """
    Persistence for process coordination and lifecycle flags.

    Typical file-based layout:
        - PID file: identifies the running instance.
        - STOP flag file: graceful stop request.
    """

    @abc.abstractmethod
    def state_dir(self) -> str:
        """Return the absolute path to the state directory."""
        raise NotImplementedError

    @abc.abstractmethod
    def read_pid(self) -> Optional[int]:
        """Read the stored PID, or None if absent/invalid."""
        raise NotImplementedError

    @abc.abstractmethod
    def write_pid(self, pid: int) -> None:
        """Persist the current process ID."""
        raise NotImplementedError

    @abc.abstractmethod
    def clear_pid(self) -> None:
        """Remove the PID record if it exists (best-effort)."""
        raise NotImplementedError

    @abc.abstractmethod
    def has_stop(self) -> bool:
        """Return True if a graceful stop has been requested."""
        raise NotImplementedError

    @abc.abstractmethod
    def set_stop(self) -> None:
        """Create the stop flag."""
        raise NotImplementedError

    @abc.abstractmethod
    def clear_stop(self) -> None:
        """Remove the stop flag (best-effort)."""
        raise NotImplementedError


class TimePort(abc.ABC):
    """
    Abstract clock for better testability and deterministic behavior.
    """

    @abc.abstractmethod
    def now(self) -> float:
        """Return current time in seconds since the epoch (time.time()-like)."""
        raise NotImplementedError

    @abc.abstractmethod
    def sleep(self, seconds: float) -> None:
        """Suspend execution for the given duration (seconds)."""
        raise NotImplementedError


class ProcessProbePort(abc.ABC):
    """
    Cross-platform process liveness probing.

    Implementations:
        - PosixProcessProbe: uses os.kill(pid, 0)
        - WindowsProcessProbe: uses os.kill or win32 APIs
    """

    @abc.abstractmethod
    def is_alive(self, pid: Optional[int]) -> bool:
        """
        Return True if 'pid' represents a currently running process.

        Args:
            pid: Process ID to probe; None returns False.
        """
        raise NotImplementedError


class DaemonManagerPort(abc.ABC):
    """
    Spawns a detached/background instance that executes the 'run' command
    with the resolved arguments. This isolates platform-specific details
    (Windows creation flags vs POSIX start_new_session, etc.).
    """

    @abc.abstractmethod
    def spawn_run(self, argv: list[str]) -> None:
        """
        Launch the background process for the 'run' subcommand.

        Args:
            argv: Full argument vector to execute (including program name).
        """
        raise NotImplementedError
