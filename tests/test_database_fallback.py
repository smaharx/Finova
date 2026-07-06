import os
import importlib


def test_database_fallback(monkeypatch, tmp_path):
    # Ensure DATABASE_URL is not set in the environment for this test
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Reload the module to pick up environment changes
    import api.database as db_module
    importlib.reload(db_module)

    assert db_module.DATABASE_URL.startswith("sqlite:///"), "DATABASE_URL should fall back to sqlite when unset"
