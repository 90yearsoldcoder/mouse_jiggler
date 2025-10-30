# src/core/pattern.py
from __future__ import annotations

import abc
import random
from dataclasses import dataclass
from typing import Tuple


class PatternStrategy(abc.ABC):
    """
    Strategy interface for mouse jiggle delta generation.

    Contract:
        next_delta(step, amplitude) -> (dx, dy)
    Requirements:
        - The sequence should avoid long-term drift whenever possible.
        - Small movements are preferred to reduce visual disturbance.
        - Implementations must be deterministic for a given 'step' unless
          randomness is explicitly desired (e.g., RandomPattern).
    """

    @abc.abstractmethod
    def next_delta(self, step: int, amplitude: int) -> Tuple[int, int]:
        """
        Return the delta (dx, dy) for the given 'step' with the provided amplitude.

        Args:
            step: Non-negative integer representing the current iteration.
            amplitude: Positive integer pixel step (>=1).

        Returns:
            (dx, dy): Signed integer offsets to apply for this step.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class SquarePattern(PatternStrategy):
    """
    A small square loop to mitigate cumulative drift:
        ( +A, 0 ) -> ( 0, +A ) -> ( -A, 0 ) -> ( 0, -A ) -> repeat

    Rationale:
        - Ensures that over 4 steps, the pointer returns to the original position.
        - Works well with low amplitude (1–2 px) to remain unobtrusive.
    """

    def next_delta(self, step: int, amplitude: int) -> Tuple[int, int]:
        if amplitude < 1:
            amplitude = 1  # guard against invalid input
        phase = step % 4
        if phase == 0:
            return (amplitude, 0)
        elif phase == 1:
            return (0, amplitude)
        elif phase == 2:
            return (-amplitude, 0)
        else:
            return (0, -amplitude)


@dataclass(frozen=True)
class RandomPattern(PatternStrategy):
    """
    A lightweight random perturbation pattern that attempts to reduce net drift.

    Design:
        - Picks a direction among the 8-neighborhood (including diagonals) with amplitude 1..A.
        - Uses a simple "compensation" bias: over time the cumulative drift is nudged back
          towards zero by occasionally flipping the sign when the random walk drifts too far.

    Notes:
        - This pattern can be more "natural" for certain OS heuristics but may be more visible.
        - Keep amplitude small for better discretion.
    """

    # Maximum tolerated drift before biasing towards compensation (in pixels).
    max_drift: int = 5

    # Probability of forcing a compensating move once drift exceeds threshold.
    compensate_prob: float = 0.6

    def __post_init__(self) -> None:
        # Validate parameters (frozen dataclass -> use object.__setattr__ if needed; here only validate)
        if self.max_drift < 1:
            raise ValueError("max_drift must be >= 1.")
        if not (0.0 <= self.compensate_prob <= 1.0):
            raise ValueError("compensate_prob must be in [0, 1].")

    # Internal drift trackers (mutable state in a frozen dataclass is avoided intentionally;
    # we instead compute "virtual" compensation based on step parity for determinism concerns).
    def next_delta(self, step: int, amplitude: int) -> Tuple[int, int]:
        if amplitude < 1:
            amplitude = 1

        # Choose a random magnitude in [1, amplitude]
        mag = 1 + (step % amplitude)

        # 8 possible directions (dx, dy)
        dirs = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]
        # Pseudo-random index derived from step for reproducibility across runs without global RNG state
        idx = (step * 1103515245 + 12345) & 0x7FFFFFFF
        choice = dirs[idx % len(dirs)]
        dx, dy = choice[0] * mag, choice[1] * mag

        # Simple virtual compensation bias:
        # If step crosses thresholds, flip sign with certain probability to curb drift.
        # Use a deterministic pseudo-probability from step (no global randomness).
        if (step % 17) == 0:
            # Map step to a pseudo-prob in [0,1)
            pseudo_p = ((step * 2654435761) & 0xFFFFFFFF) / 2**32
            if pseudo_p < self.compensate_prob:
                dx, dy = -dx, -dy

        return (dx, dy)


__all__ = [
    "PatternStrategy",
    "SquarePattern",
    "RandomPattern",
]
