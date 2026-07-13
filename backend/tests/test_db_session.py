"""Database engine pool bounds for local API and child-worker coexistence."""

from app.db import session


def test_postgres_engine_options_use_conservative_bounded_pool(monkeypatch):
    monkeypatch.setattr(session.settings, "db_pool_size", 3)
    monkeypatch.setattr(session.settings, "db_max_overflow", 1)
    monkeypatch.setattr(session.settings, "db_pool_timeout_seconds", 10)

    assert session._engine_options("postgresql://example.invalid/db") == {
        "pool_pre_ping": True,
        "pool_size": 3,
        "max_overflow": 1,
        "pool_timeout": 10,
        "pool_recycle": 300,
    }


def test_sqlite_engine_options_do_not_pass_queue_pool_arguments():
    assert session._engine_options("sqlite:///:memory:") == {"pool_pre_ping": True}
