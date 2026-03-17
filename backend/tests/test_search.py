import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.api_key import APIKey
from app.models.product import Product
from app.services.auth import generate_api_key, get_current_api_key


def make_mock_api_key() -> APIKey:
    raw_key, key_hash = generate_api_key()
    api_key = MagicMock(spec=APIKey)
    api_key.id = uuid.uuid4()
    api_key.key_hash = key_hash
    api_key.name = "Test Key"
    api_key.owner_email = "test@example.com"
    api_key.policy = {}
    api_key.is_active = True
    return api_key


def make_mock_product(**kwargs) -> MagicMock:  # type: ignore[no-untyped-def]
    from datetime import datetime

    product = MagicMock(spec=Product)
    product.id = kwargs.get("id", uuid.uuid4())
    product.name = kwargs.get("name", "Test Product")
    product.description = kwargs.get("description", None)
    product.price = kwargs.get("price", 1000)
    product.category = kwargs.get("category", "electronics")
    product.in_stock = kwargs.get("in_stock", True)
    product.stock_qty = kwargs.get("stock_qty", 10)
    product.delivery_days = kwargs.get("delivery_days", 3)
    product.attributes = kwargs.get("attributes", {})
    product.created_at = kwargs.get("created_at", datetime(2024, 1, 1))
    product.updated_at = kwargs.get("updated_at", datetime(2024, 1, 1))
    return product


@pytest.fixture
def client_with_auth() -> TestClient:
    api_key = make_mock_api_key()

    async def override_auth() -> APIKey:
        return api_key

    app.dependency_overrides[get_current_api_key] = override_auth
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_search_requires_auth() -> None:
    client = TestClient(app)
    resp = client.post("/v1/search", json={})
    assert resp.status_code == 401


def test_search_empty_returns_hint(client_with_auth: TestClient) -> None:
    mock_scalar = MagicMock()
    mock_scalar.scalar_one.return_value = 0

    mock_products = MagicMock()
    mock_products.scalars.return_value.all.return_value = []

    execute_calls = [mock_scalar, mock_products]
    call_index = 0

    async def mock_execute(query):  # type: ignore[no-untyped-def]
        nonlocal call_index
        result = execute_calls[call_index % len(execute_calls)]
        call_index += 1
        return result

    with patch("app.routers.search.AsyncSession.execute", side_effect=mock_execute):
        with patch("app.database.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute.side_effect = [mock_scalar, mock_products]
            mock_db.return_value.__aiter__ = AsyncMock(return_value=iter([mock_session]))

            # Use override for db as well
            from app.database import get_db

            async def override_db():  # type: ignore[no-untyped-def]
                yield mock_session

            app.dependency_overrides[get_db] = override_db
            resp = client_with_auth.post("/v1/search", json={})
            app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert "agent_hint" in data
    assert "0件" in data["agent_hint"]


def test_search_with_results(client_with_auth: TestClient) -> None:
    products = [make_mock_product(), make_mock_product()]

    mock_count = MagicMock()
    mock_count.scalar_one.return_value = 2

    mock_list = MagicMock()
    mock_list.scalars.return_value.all.return_value = products

    async def mock_execute(query):  # type: ignore[no-untyped-def]
        # First call = count, second = list
        if not hasattr(mock_execute, "_called"):
            mock_execute._called = True
            return mock_count
        return mock_list

    from app.database import get_db

    async def override_db():  # type: ignore[no-untyped-def]
        mock_session = AsyncMock()
        mock_session.execute.side_effect = [mock_count, mock_list]
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    resp = client_with_auth.post("/v1/search", json={"limit": 10, "offset": 0})
    app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["products"]) == 2
    assert "agent_hint" in data
