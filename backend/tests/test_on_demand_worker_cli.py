"""Guarded on-demand worker CLI routing tests."""

import uuid

from app.core import on_demand_worker
from app.core.on_demand_briefing import ProcessResult


class _Session:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_request_id_runs_only_the_targeted_request(monkeypatch):
    request_id = uuid.uuid4()
    session = _Session()
    calls = []

    monkeypatch.setattr(
        on_demand_worker,
        "build_arg_parser",
        lambda: _Parser(request_id=request_id),
    )
    monkeypatch.setattr(on_demand_worker, "ensure_local_dev_write_allowed", lambda *_: None)
    monkeypatch.setattr(on_demand_worker, "build_openai_client", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(on_demand_worker, "get_session_factory", lambda: lambda: session)
    monkeypatch.setattr(
        on_demand_worker,
        "process_v8_request",
        lambda db, target, client, model, **kwargs: calls.append(
            (db, target, client, model, kwargs)
        )
        or ProcessResult(request_id=target, state="succeeded"),
    )
    monkeypatch.setattr(
        on_demand_worker,
        "run_pending_v8_requests",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("queue scan must not run")),
    )
    monkeypatch.setattr(on_demand_worker.settings, "database_url", "postgresql://configured")
    monkeypatch.setattr(on_demand_worker.settings, "ai_api_key", "configured")

    assert on_demand_worker.main() == 0
    assert calls[0][0] is session
    assert calls[0][1] == request_id
    assert callable(calls[0][4]["context_refresher"])
    assert session.closed is True


def test_request_id_follows_context_refresh_successor(monkeypatch):
    request_id = uuid.uuid4()
    successor_id = uuid.uuid4()
    session = _Session()
    calls = []

    monkeypatch.setattr(
        on_demand_worker,
        "build_arg_parser",
        lambda: _Parser(request_id=request_id),
    )
    monkeypatch.setattr(on_demand_worker, "ensure_local_dev_write_allowed", lambda *_: None)
    monkeypatch.setattr(on_demand_worker, "build_openai_client", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(on_demand_worker, "get_session_factory", lambda: lambda: session)

    def process(_db, target, _client, _model, **_kwargs):
        calls.append(target)
        if target == request_id:
            return ProcessResult(
                request_id=target,
                state="failed",
                successor_request_id=successor_id,
            )
        return ProcessResult(request_id=target, state="succeeded")

    monkeypatch.setattr(on_demand_worker, "process_v8_request", process)
    monkeypatch.setattr(on_demand_worker.settings, "database_url", "postgresql://configured")
    monkeypatch.setattr(on_demand_worker.settings, "ai_api_key", "configured")

    assert on_demand_worker.main() == 0
    assert calls == [request_id, successor_id]


class _Parser:
    def __init__(self, *, request_id):
        self.request_id = request_id

    def parse_args(self):
        return type(
            "Args",
            (),
            {
                "request_id": self.request_id,
                "max_requests": 10,
                "confirm_local_dev_write": True,
            },
        )()
