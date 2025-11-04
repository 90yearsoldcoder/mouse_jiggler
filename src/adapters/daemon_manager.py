# src/adapters/daemon_manager.py
from __future__ import annotations

import os
import subprocess
from typing import List
from ..core.ports import DaemonManagerPort


class SubprocessDaemonManager(DaemonManagerPort):
    """
    Spawns a detached subprocess that runs the 'run' subcommand.

    Design:
        - Redirects stdio to os.devnull for true background behavior.
        - Uses Windows creation flags or POSIX start_new_session for detachment.
    """

    def spawn_run(self, argv: List[str]) -> None:
        # Detach stdio
        with open(os.devnull, "wb") as devnull:
            kwargs = {"stdin": devnull, "stdout": devnull, "stderr": devnull}

            if os.name == "nt":
                # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                kwargs["creationflags"] = 0x00000008 | 0x00000200
            else:
                # New session on POSIX
                kwargs["start_new_session"] = True

            subprocess.Popen(argv, **kwargs)
