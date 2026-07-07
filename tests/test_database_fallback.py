import importlib


def test_database_fallback(monkeypatch):
    # Prevent dotenv from loading a .env file during this test so import sees an empty env
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)

    # Ensure DATABASE_URL is not set in the environment for this test
    monkeypatch.delenv("DATABASE_URL", raising=False)

    # Import / reload the module so it picks up the test environment
    import api.database as db_module

    importlib.reload(db_module)

    assert db_module.DATABASE_URL.startswith("sqlite:///"), (
        "DATABASE_URL should fall back to sqlite when unset"
    )
