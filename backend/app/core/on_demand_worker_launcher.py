"""Launch the guarded on-demand worker as an isolated child process.

The API may start this process after committing a generation request, but it
does not import a provider client or perform generation work itself.
"""

import logging
import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_AUTO_LAUNCH_ENVS = {"local", "dev", "development"}


def _reap_worker(process: subprocess.Popen[bytes]) -> None:
    """Wait for a child worker so completed processes do not become zombies."""
    return_code = process.wait()
    if return_code != 0:
        logger.warning(
            "On-demand worker process exited unsuccessfully: pid=%s return_code=%s",
            process.pid,
            return_code,
        )


def launch_on_demand_worker(request_id: uuid.UUID, *, env: str) -> bool:
    """Start one request-scoped worker without blocking the API response."""
    if env.strip().lower() not in _AUTO_LAUNCH_ENVS:
        logger.warning(
            "On-demand worker auto-launch skipped outside local/development: env=%s",
            env,
        )
        return False

    command = [
        sys.executable,
        "-m",
        "app.core.on_demand_worker",
        "--request-id",
        str(request_id),
        "--confirm-local-dev-write",
    ]
    try:
        process = subprocess.Popen(
            command,
            cwd=_BACKEND_ROOT,
            close_fds=True,
            start_new_session=os.name == "posix",
        )
    except OSError:
        logger.exception(
            "Failed to launch the on-demand worker; request remains queued: request_id=%s",
            request_id,
        )
        return False

    threading.Thread(target=_reap_worker, args=(process,), daemon=True).start()
    logger.info(
        "Launched isolated on-demand worker: request_id=%s pid=%s",
        request_id,
        process.pid,
    )
    return True
