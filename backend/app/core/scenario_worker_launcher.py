"""Launch one guarded scenario worker outside the public API process."""

import logging
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_AUTO_LAUNCH_ENVS = {"local", "dev", "development"}
_LAUNCH_COOLDOWN_SECONDS = 20.0
_MAX_LAUNCH_ATTEMPTS = 3
_launch_lock = threading.Lock()
_launch_state: dict[uuid.UUID, tuple[float, int]] = {}


def reset_launch_state() -> None:
    """Clear process-local recovery state for tests and controlled restarts."""
    with _launch_lock:
        _launch_state.clear()


def _reap_worker(process: subprocess.Popen[bytes]) -> None:
    """Wait for a child process and report only non-sensitive outcome data."""
    return_code = process.wait()
    if return_code != 0:
        logger.warning(
            "Scenario worker process exited unsuccessfully: pid=%s return_code=%s",
            process.pid,
            return_code,
        )


def launch_scenario_worker(
    request_id: uuid.UUID,
    *,
    env: str,
    allow_production: bool = False,
    now: float | None = None,
) -> bool:
    """Start one request-scoped worker only in an approved local environment."""
    normalized_env = env.strip().lower()
    if normalized_env not in _AUTO_LAUNCH_ENVS and not (
        normalized_env == "production" and allow_production
    ):
        logger.warning(
            "Scenario worker auto-launch skipped outside local/development: env=%s",
            env,
        )
        return False

    launched_at = time.monotonic() if now is None else now
    with _launch_lock:
        previous_at, attempts = _launch_state.get(request_id, (float("-inf"), 0))
        if attempts >= _MAX_LAUNCH_ATTEMPTS:
            return False
        if launched_at - previous_at < _LAUNCH_COOLDOWN_SECONDS:
            return False
        _launch_state[request_id] = (launched_at, attempts + 1)

    command = [
        sys.executable,
        "-m",
        "app.core.scenario_worker",
        "--request-id",
        str(request_id),
        "--confirm-generation-write",
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
            "Failed to launch the scenario worker; request remains queued: request_id=%s",
            request_id,
        )
        return False

    threading.Thread(target=_reap_worker, args=(process,), daemon=True).start()
    logger.info(
        "Launched isolated scenario worker: request_id=%s pid=%s",
        request_id,
        process.pid,
    )
    return True
