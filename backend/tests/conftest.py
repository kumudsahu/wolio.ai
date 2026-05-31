"""Pytest fixtures — run the whole API against an isolated temp database."""
import os
import tempfile
import pathlib
import pytest

# Point the data layer at a throwaway DB BEFORE the app imports it.
_tmp = pathlib.Path(tempfile.gettempdir()) / "wolio_test.db"
if _tmp.exists():
    _tmp.unlink()
os.environ["WOLIO_DB"] = str(_tmp)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.db import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _db():
    init_db()
    yield
    if _tmp.exists():
        _tmp.unlink()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def child(client):
    """Create an onboarded child and return its id."""
    r = client.post("/api/onboarding", json={
        "name": "Tester", "age_group": "9-12",
        "interests": ["space", "games", "stories"], "learning_style": "games",
    })
    assert r.status_code == 200
    return r.json()["user_id"]
