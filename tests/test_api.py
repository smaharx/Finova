import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force tests to use an isolated SQLite database.
os.environ["DATABASE_URL"] = "sqlite:///./test_finance_tracker.db"

from api.database import Base, get_db  # noqa: E402
from api.main import app  # noqa: E402

TEST_ENGINE = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db() -> Generator:
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client() -> Generator:
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "online"
    assert "message" in data
    assert "ai_model_loaded" in data


def test_create_transaction(client):
    payload = {
        "date": "2026-01-01",
        "description": "Netflix subscription",
        "amount": 15.99,
    }

    response = client.post("/transactions", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Transaction successfully committed to cloud database."
    assert "data" in data

    txn = data["data"]
    assert txn["description"] == payload["description"]
    assert txn["amount"] == payload["amount"]
    assert "id" in txn
    assert "category" in txn


def test_get_transactions(client):
    response = client.get("/transactions")
    assert response.status_code == 200

    data = response.json()
    assert "count" in data
    assert "transactions" in data
    assert isinstance(data["transactions"], list)


def test_update_transaction(client):
    create_response = client.post(
        "/transactions",
        json={
            "date": "2026-01-02",
            "description": "Uber ride",
            "amount": 9.5,
        },
    )
    assert create_response.status_code == 200

    txn_id = create_response.json()["data"]["id"]

    update_payload = {
        "date": "2026-01-03",
        "description": "Uber ride updated",
        "amount": 12.0,
        "category": "Transport",
    }

    response = client.put(f"/transactions/{txn_id}", json=update_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Transaction updated successfully."
    assert data["data"]["description"] == "Uber ride updated"
    assert data["data"]["amount"] == 12.0
    assert data["data"]["category"] == "Transport"


def test_delete_transaction(client):
    create_response = client.post(
        "/transactions",
        json={
            "date": "2026-01-04",
            "description": "Temporary item",
            "amount": 20.0,
        },
    )
    assert create_response.status_code == 200

    txn_id = create_response.json()["data"]["id"]

    delete_response = client.delete(f"/transactions/{txn_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_id"] == txn_id

    get_response = client.get("/transactions")
    assert get_response.status_code == 200
    transactions = get_response.json()["transactions"]
    assert all(txn["id"] != txn_id for txn in transactions)


def test_correction_flow(client):
    create_response = client.post(
        "/transactions",
        json={
            "date": "2026-01-05",
            "description": "ChatGPT subscription",
            "amount": 20.0,
        },
    )
    assert create_response.status_code == 200

    txn_id = create_response.json()["data"]["id"]

    correction_response = client.post(
        f"/transactions/{txn_id}/correction",
        json={
            "corrected_category": "Subscriptions",
            "notes": "This is a monthly software subscription.",
        },
    )
    assert correction_response.status_code == 200

    data = correction_response.json()
    assert data["message"] == "Correction saved successfully."
    assert data["transaction"]["category"] == "Subscriptions"


def test_summary_endpoint(client):
    response = client.get("/analytics/summary")
    assert response.status_code == 200

    data = response.json()
    assert "overall" in data
    assert "categorical_breakdown" in data
    assert "total_spent" in data["overall"]
    assert "transaction_count" in data["overall"]


def test_filtered_transactions(client):
    response = client.get("/transactions", params={"search": "Netflix"})
    assert response.status_code == 200

    data = response.json()
    assert "transactions" in data
    for txn in data["transactions"]:
        assert "netflix" in txn["description"].lower()
