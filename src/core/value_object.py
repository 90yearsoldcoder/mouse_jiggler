# src/core/value_objects.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class ValueErrorSpec(Exception):
    """Raised when a human-readable time or amplitude spec is invalid."""


def _parse_time_spec_to_seconds(spec: str) -> float:
    """
    Parse a human-readable time specification into seconds (float).

    Supported suffixes:
        - "ms": milliseconds
        - "s" : seconds
        - "m" : minutes
        - "h" : hours
    Bare numbers are treated as seconds.

    Examples:
        "500ms" -> 0.5
        "2s"    -> 2.0
        "3m"    -> 180.0
        "1h"    -> 3600.0
        "5"     -> 5.0  (seconds)

    Raises:
        ValueErrorSpec: if the spec is empty or non-numeric.
    """
    if spec is None:
        raise ValueErrorSpec("Time spec cannot be None.")
    s = spec.strip().lower()
    if not s:
        raise ValueErrorSpec("Time spec cannot be empty.")

    try:
        if s.endswith("ms"):
            return float(s[:-2]) / 1000.0
        if s.endswith("s"):
            return float(s[:-1])
        if s.endswith("m"):
            return float(s[:-1]) * 60.0
        if s.endswith("h"):
            return float(s[:-1]) * 3600.0
        # bare number -> seconds
        return float(s)
    except ValueError as e:
        raise ValueErrorSpec(f"Invalid time spec: {spec!r}") from e


@dataclass(frozen=True)
class Interval:
    """
    Represents the jiggle interval (seconds as positive float).

    Designed to be constructed from a human-readable spec (e.g., "500ms", "2s").
    """
    seconds: float

    @staticmethod
    def from_spec(spec: str) -> "Interval":
        secs = _parse_time_spec_to_seconds(spec)
        if secs <= 0:
            raise ValueErrorSpec(f"Interval must be > 0 seconds, got {secs}.")
        return Interval(seconds=secs)

    def __str__(self) -> str:
        # Prefer human-friendly output; keep it simple (seconds with up to 3 decimals).
        return f"{self.seconds:.3f}s"


@dataclass(frozen=True)
class Duration:
    """
    Represents the total running duration (seconds as positive float), or None for infinite.

    Note:
        Use `Duration.none()` to represent an infinite duration (i.e., run until stopped).
    """
    seconds: Optional[float]

    @staticmethod
    def from_spec(spec: Optional[str]) -> "Duration":
        if spec is None:
            return Duration.none()
        secs = _parse_time_spec_to_seconds(spec)
        if secs <= 0:
            raise ValueErrorSpec(f"Duration must be > 0 seconds, got {secs}.")
        return Duration(seconds=secs)

    @staticmethod
    def none() -> "Duration":
        return Duration(seconds=None)

    def is_infinite(self) -> bool:
        return self.seconds is None

    def __str__(self) -> str:
        return "infinite" if self.is_infinite() else f"{self.seconds:.3f}s"


@dataclass(frozen=True)
class Amplitude:
    """
    Represents the jiggle pixel step (positive integer).

    Rationale:
        A small amplitude (1–2 px) minimizes visual disturbance while still
        generating sufficient input activity on most desktop environments.
    """
    pixels: int

    @staticmethod
    def from_int(pixels: int) -> "Amplitude":
        if not isinstance(pixels, int):
            raise ValueErrorSpec("Amplitude must be an integer.")
        if pixels <= 0:
            raise ValueErrorSpec(f"Amplitude must be >= 1, got {pixels}.")
        return Amplitude(pixels=pixels)

    def __str__(self) -> str:
        return f"{self.pixels}px"


__all__ = [
    "ValueErrorSpec",
    "Interval",
    "Duration",
    "Amplitude",
]
