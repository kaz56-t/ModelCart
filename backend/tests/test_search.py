import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey
from app.models.product import Product
from app.services.auth import hash_api_key

RAW_KEY = "sk-agent-searchtest"


async def setup_key(db: AsyncSession) -> None:
    api_key = APIKey(
        key_hash=hash_api_key(RAW_KEY),
        name="search-test",
        owner_email="search@example.com",
        policy={},
    )
    db.add(api_key)
    await db.commit()


async def create_product(db: AsyncSession, **kwargs) -> Product:  # type: ignore[return]
    defaults = {
        "name": "Test Product",
        "description": "A test product",
        "price": 1000,
        "category": "electronics",
        "in_stock": True,
        "stock_qty": 10,
        "delivery_days": 3,
        "attributes": {},
    }
    defaults.update(kwargs)
    product = Product(**defaults)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest.mark.asyncio
async def test_search_requires_auth(client: AsyncClient):
    resp = await client.post("/v1/search", json={})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_search_empty(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    resp = await client.post(
        "/v1/search", json={}, headers={"Authorization": f"Bearer {RAW_KEY}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert "agent_hint" in data


@pytest.mark.asyncio
async def test_search_keyword(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    await create_product(db_session, name="Laptop Pro", category="electronics")
    await create_product(db_session, name="Coffee Mug", category="kitchen")

    resp = await client.post(
        "/v1/search",
        json={"keyword": "Laptop"},
        headers={"Authorization": f"Bearer {RAW_KEY}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Laptop Pro"


@pytest.mark.asyncio
async def test_search_category_filter(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    await create_product(db_session, name="Phone", category="electronics")
    await create_product(db_session, name="Book", category="books")

    resp = await client.post(
        "/v1/search",
        json={"category": "books"},
        headers={"Authorization": f"Bearer {RAW_KEY}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Book"


@pytest.mark.asyncio
async def test_search_price_filter(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    await create_product(db_session, name="Cheap", price=500, category="misc")
    await create_product(db_session, name="Expensive", price=5000, category="misc")

    resp = await client.post(
        "/v1/search",
        json={"min_price": 1000, "max_price": 9999},
        headers={"Authorization": f"Bearer {RAW_KEY}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Expensive"


@pytest.mark.asyncio
async def test_search_in_stock_filter(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    await create_product(db_session, name="InStock", in_stock=True, category="misc")
    await create_product(db_session, name="OutOfStock", in_stock=False, category="misc")

    resp = await client.post(
        "/v1/search",
        json={"in_stock": True},
        headers={"Authorization": f"Bearer {RAW_KEY}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "InStock"


@pytest.mark.asyncio
async def test_search_delivery_days_filter(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    await create_product(db_session, name="Fast", delivery_days=1, category="misc")
    await create_product(db_session, name="Slow", delivery_days=10, category="misc")

    resp = await client.post(
        "/v1/search",
        json={"max_delivery_days": 3},
        headers={"Authorization": f"Bearer {RAW_KEY}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Fast"


@pytest.mark.asyncio
async def test_search_pagination(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    for i in range(5):
        await create_product(db_session, name=f"Product {i}", category="misc")

    resp = await client.post(
        "/v1/search",
        json={"limit": 2, "offset": 0},
        headers={"Authorization": f"Bearer {RAW_KEY}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_search_agent_hint_present(client: AsyncClient, db_session: AsyncSession):
    await setup_key(db_session)
    await create_product(db_session, name="Widget", category="misc")

    resp = await client.post(
        "/v1/search",
        json={},
        headers={"Authorization": f"Bearer {RAW_KEY}"},
    )
    assert resp.status_code == 200
    assert resp.json()["agent_hint"] != ""
