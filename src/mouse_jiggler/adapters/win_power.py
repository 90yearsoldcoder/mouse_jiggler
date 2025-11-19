# src/adapters/win_power.py
from ctypes import windll, c_uint

# Flags
ES_CONTINUOUS        = 0x80000000
ES_SYSTEM_REQUIRED   = 0x00000001
ES_DISPLAY_REQUIRED  = 0x00000002

class WindowsPowerInhibitor:
    """
    Prevent Windows from entering sleep or turning off the display.
    Usage:
        inhibitor = WindowsPowerInhibitor()
        inhibitor.activate()
        ... do work ...
        inhibitor.release()
    """
    def __init__(self):
        self._active = False

    def activate(self):
        if not self._active:
            windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            self._active = True

    def release(self):
        if self._active:
            windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            self._active = False
