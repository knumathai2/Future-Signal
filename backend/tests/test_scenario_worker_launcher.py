"""Request-scoped scenario worker launcher tests."""

import uuid

import pytest

from app.core import scenario_worker_launcher as launcher


class _FakeProcess:
    pid = 2468

    def wait(self):
        return 0


class _FakeThread:
    def __init__(self, *, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False

    def start(self):
        self.started = True


@pytest.fixture(autouse=True)
def clean_launch_state():
    launcher.reset_launch_state()
    yield
    launcher.reset_launch_state()


def test_launcher_starts_request_scoped_detached_worker(monkeypatch):
    request_id = uuid.uuid4()
    calls = []
    threads = []

    def fake_popen(command, **kwargs):
        calls.append((command, kwargs))
        return _FakeProcess()

    def fake_thread(**kwargs):
        thread = _FakeThread(**kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(launcher.threading, "Thread", fake_thread)

    assert launcher.launch_scenario_worker(request_id, env="local") is True
    command, kwargs = calls[0]
    assert command == [
        launcher.sys.executable,
        "-m",
        "app.core.scenario_worker",
        "--request-id",
        str(request_id),
        "--confirm-local-dev-write",
    ]
    assert kwargs["cwd"] == launcher._BACKEND_ROOT
    assert kwargs["close_fds"] is True
    assert kwargs["start_new_session"] == (launcher.os.name == "posix")
    assert threads[0].daemon is True
    assert threads[0].started is True


def test_launcher_refuses_non_development_environment(monkeypatch):
    def unexpected_popen(*_args, **_kwargs):
        raise AssertionError("worker must not start")

    monkeypatch.setattr(launcher.subprocess, "Popen", unexpected_popen)

    assert launcher.launch_scenario_worker(uuid.uuid4(), env="production") is False


def test_launcher_leaves_request_recoverable_when_spawn_fails(monkeypatch):
    def failed_popen(*_args, **_kwargs):
        raise OSError("spawn unavailable")

    monkeypatch.setattr(launcher.subprocess, "Popen", failed_popen)

    assert launcher.launch_scenario_worker(uuid.uuid4(), env="development") is False


def test_launcher_cooldown_and_attempt_cap_prevent_spawn_storm(monkeypatch):
    request_id = uuid.uuid4()
    calls = []

    monkeypatch.setattr(
        launcher.subprocess,
        "Popen",
        lambda command, **kwargs: calls.append((command, kwargs)) or _FakeProcess(),
    )
    monkeypatch.setattr(launcher.threading, "Thread", lambda **kwargs: _FakeThread(**kwargs))

    assert launcher.launch_scenario_worker(request_id, env="local", now=0) is True
    assert launcher.launch_scenario_worker(request_id, env="local", now=10) is False
    assert launcher.launch_scenario_worker(request_id, env="local", now=21) is True
    assert launcher.launch_scenario_worker(request_id, env="local", now=42) is True
    assert launcher.launch_scenario_worker(request_id, env="local", now=63) is False
    assert len(calls) == 3


def test_reaper_logs_nonzero_exit_without_raising(caplog):
    class FailedProcess:
        pid = 1357

        def wait(self):
            return 1

    launcher._reap_worker(FailedProcess())

    assert "return_code=1" in caplog.text
