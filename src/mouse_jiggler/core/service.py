# src/core/service.py
from __future__ import annotations

import os
import sys
import time
import signal
import subprocess
from dataclasses import dataclass
from typing import Optional

from mouse_jiggler.core.value_object import Interval, Duration, Amplitude
from mouse_jiggler.core.patterns import PatternStrategy, SquarePattern
from mouse_jiggler.core.ports import (
    MousePort,
    StateRepoPort,
    TimePort,
    ProcessProbePort,
    DaemonManagerPort,
)


@dataclass(frozen=True)
class JigglerConfig:
    """
    Immutable configuration for one jiggler session.
    """
    interval: Interval
    amplitude: Amplitude
    duration: Duration
    pattern: PatternStrategy = SquarePattern()


class JigglerService:
    """
    Core orchestration logic for start/run/stop/status.

    This class is pure application logic, depending only on abstract ports.
    """

    def __init__(
        self,
        mouse: MousePort,
        repo: StateRepoPort,
        clock: TimePort,
        probe: ProcessProbePort,
        daemon: DaemonManagerPort,
    ):
        self.mouse = mouse
        self.repo = repo
        self.clock = clock
        self.probe = probe
        self.daemon = daemon

    # ------------------------------
    # Public commands
    # ------------------------------

    def start(self, cfg: JigglerConfig, force: bool = False) -> None:
        """
        Launch a background 'run' process if none is active.
        """
        pid = self.repo.read_pid()
        if pid and self.probe.is_alive(pid):
            if not force:
                print(f"Already running (pid={pid}). Use --force to override.", file=sys.stderr)
                sys.exit(1)
            else:
                self.repo.clear_pid()

        # Compose argv for background process
        if getattr(sys, "frozen", False):
            # Running as a bundled executable
            argv = [
                sys.executable,
                "run",
                "--interval", f"{cfg.interval.seconds}s",
                "--amplitude", str(cfg.amplitude.pixels),
            ]
        else:
            # Running via Python module
            argv = [
                sys.executable,
                "-m", "mouse_jiggler.cli",
                "run",
                "--interval", f"{cfg.interval.seconds}s",
                "--amplitude", str(cfg.amplitude.pixels),
            ]
        if not cfg.duration.is_infinite():
            argv += ["--duration", f"{cfg.duration.seconds}s"]

        print(argv)  # Debug output
        self.daemon.spawn_run(argv)

        # Wait briefly for pid file confirmation
        for _ in range(20):
            self.clock.sleep(0.1)
            pid = self.repo.read_pid()
            if pid and self.probe.is_alive(pid):
                print(f"Started mouse jiggler (pid={pid}).")
                return
        print("Launched, but PID not confirmed. Use `status` to check.", file=sys.stderr)

    def run(self, cfg: JigglerConfig) -> None:
        """
        Execute the main jiggle loop in foreground.

        On Windows, this also requests the system to stay awake (no sleep,
        no display off) while the jiggler is running.
        """
        self.repo.write_pid(os.getpid())
        self.repo.clear_stop()

        # Graceful cleanup on signals
        def cleanup(*_):
            self.repo.clear_pid()
            self.repo.clear_stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, cleanup)

        interval = cfg.interval.seconds
        amp = cfg.amplitude.pixels
        duration = cfg.duration.seconds
        deadline = None if cfg.duration.is_infinite() else self.clock.now() + duration

        # Optional: prevent system sleep on Windows
        inhibitor = None
        if os.name == "nt":
            try:
                # Local import to avoid hard dependency at module import time
                from mouse_jiggler.adapters.win_power import WindowsPowerInhibitor
                inhibitor = WindowsPowerInhibitor()
                inhibitor.activate()
            except Exception:
                inhibitor = None  # If this fails, just continue without power inhibit

        step = 0
        try:
            while True:
                # Check stop flag and deadline
                if self.repo.has_stop():
                    break
                now = self.clock.now()
                if deadline and now >= deadline:
                    break

                # Compute and apply delta
                dx, dy = cfg.pattern.next_delta(step, amp)
                try:
                    self.mouse.move(dx, dy)
                except Exception:
                    # Ignore transient input errors; continue the loop
                    pass

                step += 1

                # Sleep in small quanta so that 'stop' is responsive
                sleep_quantum = 0.2  # seconds
                remaining = interval
                while remaining > 0:
                    if self.repo.has_stop():
                        break
                    now = self.clock.now()
                    if deadline and now >= deadline:
                        break
                    q = sleep_quantum if remaining > sleep_quantum else remaining
                    self.clock.sleep(q)
                    remaining -= q

                # If stop/deadline triggered during inner sleep loop, break outer loop
                if self.repo.has_stop():
                    break
                if deadline and self.clock.now() >= deadline:
                    break
        finally:
            # Release Windows sleep inhibition if enabled
            if inhibitor is not None:
                try:
                    inhibitor.release()
                except Exception:
                    pass
            cleanup()

    def stop(self) -> None:
        """
        Signal the running process to stop (via STOP flag).
        """
        pid = self.repo.read_pid()
        if not pid or not self.probe.is_alive(pid):
            self.repo.clear_pid()
            self.repo.clear_stop()
            print("Not running.")
            return

        self.repo.set_stop()
        for _ in range(50):  # ~5s
            if not self.probe.is_alive(pid):
                self.repo.clear_pid()
                self.repo.clear_stop()
                print("Stopped.")
                return
            self.clock.sleep(0.1)
        print("Stop requested but process still alive. Kill manually if needed.", file=sys.stderr)

    def status(self) -> None:
        """
        Show current status of the jiggler.
        """
        pid = self.repo.read_pid()
        if pid and self.probe.is_alive(pid):
            print(f"Running (pid={pid}) in {self.repo.state_dir()}")
        else:
            print("Not running.")
