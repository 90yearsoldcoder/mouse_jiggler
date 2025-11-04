# src/cli.py
from __future__ import annotations

import argparse
import sys

from .core.value_object import Interval, Duration, Amplitude, ValueErrorSpec
from .core.patterns import SquarePattern  # can expose pattern selection later
from .core.service import JigglerConfig, JigglerService

from .adapters.system_time import SystemTime
from .adapters.fs_repo import FilesystemStateRepo
from .adapters.process_probe import SimpleProcessProbe
from .adapters.pynput_mouse import PynputMouseAdapter
from .adapters.daemon_manager import SubprocessDaemonManager


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mousejiggler",
        description="Minimal terminal-controlled mouse jiggler."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # start
    p_start = sub.add_parser("start", help="Start background jiggler")
    p_start.add_argument("--interval", default="30s", help="e.g., 500ms, 2s, 30s, 1m (default: 30s)")
    p_start.add_argument("--amplitude", type=int, default=1, help="Pixel step size (default: 1)")
    p_start.add_argument("--duration", default=None, help="Optional total duration, e.g., 15m, 2h")
    p_start.add_argument("--force", action="store_true", help="Start even if a running PID is detected")
    p_start.set_defaults(handler=_handle_start)

    # run (internal)
    p_run = sub.add_parser("run", help=argparse.SUPPRESS)
    p_run.add_argument("--interval", required=True)
    p_run.add_argument("--amplitude", type=int, required=True)
    p_run.add_argument("--duration", default=None)
    p_run.set_defaults(handler=_handle_run)

    # stop
    p_stop = sub.add_parser("stop", help="Signal the jiggler to stop")
    p_stop.set_defaults(handler=_handle_stop)

    # status
    p_status = sub.add_parser("status", help="Show running status")
    p_status.set_defaults(handler=_handle_status)

    return p


def _wire_service() -> JigglerService:
    # Instantiate real adapters
    mouse = PynputMouseAdapter()
    repo = FilesystemStateRepo()
    clock = SystemTime()
    probe = SimpleProcessProbe()
    daemon = SubprocessDaemonManager()
    return JigglerService(mouse=mouse, repo=repo, clock=clock, probe=probe, daemon=daemon)


def _parse_config(interval_spec: str, amplitude_int: int, duration_spec: str | None) -> JigglerConfig:
    try:
        interval = Interval.from_spec(interval_spec)
        amplitude = Amplitude.from_int(amplitude_int)
        duration = Duration.from_spec(duration_spec)
    except ValueErrorSpec as e:
        print(f"Invalid argument: {e}", file=sys.stderr)
        sys.exit(2)

    return JigglerConfig(
        interval=interval,
        amplitude=amplitude,
        duration=duration,
        pattern=SquarePattern(),
    )


def _handle_start(args: argparse.Namespace) -> None:
    svc = _wire_service()
    cfg = _parse_config(args.interval, args.amplitude, args.duration)
    svc.start(cfg, force=args.force)


def _handle_run(args: argparse.Namespace) -> None:
    svc = _wire_service()
    cfg = _parse_config(args.interval, args.amplitude, args.duration)
    svc.run(cfg)


def _handle_stop(_args: argparse.Namespace) -> None:
    svc = _wire_service()
    svc.stop()


def _handle_status(_args: argparse.Namespace) -> None:
    svc = _wire_service()
    svc.status()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
