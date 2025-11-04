# src/adapters/pynput_mouse.py
from __future__ import annotations

from ..core.ports import MousePort


class PynputMouseAdapter(MousePort):
    """
    Mouse adapter using 'pynput' Controller.

    Requirements:
        pip install pynput

    Platform caveats:
        - macOS requires Accessibility permission for the terminal/app.
        - Wayland sessions may restrict synthetic input.
    """

    def __init__(self) -> None:
        try:
            from pynput.mouse import Controller  # lazy import for clear error messages
        except Exception as e:
            raise RuntimeError(
                "pynput is required for mouse control. Install with 'pip install pynput'."
            ) from e
        self._ctrl = Controller()

    def move(self, dx: int, dy: int) -> None:
        # Relative movement; ignore transient errors to be resilient.
        self._ctrl.move(dx, dy)
