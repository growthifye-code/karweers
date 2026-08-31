import os
import asyncio
import pytest
import pytest_asyncio  # noqa: F401
from motor.motor_asyncio import AsyncIOMotorClient


def pytest_configure(config):
    config.option.asyncio_mode = "auto"


@pytest.fixture(autouse=True)
def _rebind_motor_client():
    """server.py imports create AsyncIOMotorClient at module load which binds
    to the FIRST event loop it sees. pytest-asyncio (auto mode) creates a
    fresh loop per test function, which invalidates that client
    ('Event loop is closed'). Rebind server.client / server.db to a fresh
    Motor client on the current loop for every test."""
    import server
    new_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    server.client = new_client
    server.db = new_client[os.environ["DB_NAME"]]
    yield
    try:
        new_client.close()
    except Exception:
        pass
