import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.api_key import APIKey
from app.services.auth import generate_api_key, get_current_api_key


def make_api_key(**kwargs: Any) -> APIKey:
    raw_key, key_hash = generate_api_key()
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "key_hash": key_hash,
        "name": "Test Key",
        "owner_email": "test@example.com",
        "policy": {
            "auto_approve_under": 0,
            "allowed_categories": [],
            "max_orders_per_day": 10,
            "max_items_per_order": 5,
            "require_dry_run": False,
        },
        "is_active": True,
        "created_at": None,
        "last_used_at": None,
    }
    defaults.update(kwargs)
    api_key = MagicMock(spec=APIKey)
    for k, v in defaults.items():
        setattr(api_key, k, v)
    return api_key, raw_key  # type: ignore[return-value]


@pytest.fixture
def api_key_and_token() -> tuple[APIKey, str]:
    return make_api_key()  # type: ignore[return-value]


@pytest.fixture
def authenticated_client(api_key_and_token: tuple[APIKey, str]) -> TestClient:
    api_key, raw_key = api_key_and_token

    async def override_get_current_api_key() -> APIKey:
        return api_key

    app.dependency_overrides[get_current_api_key] = override_get_current_api_key
    client = TestClient(app)
    yield client, raw_key
    app.dependency_overrides.clear()
