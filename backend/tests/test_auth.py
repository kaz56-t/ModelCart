import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey
from app.services.auth import hash_api_key


async def create_test_api_key(db: AsyncSession, raw_key: str = "sk-agent-testkey123") -> APIKey:
    api_key = APIKey(
        key_hash=hash_api_key(raw_key),
        name="test-key",
        owner_email="test@example.com",
        policy={},
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


@pytest.mark.asyncio
async def test_health_no_auth(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_auth_missing_token(client: AsyncClient):
    resp = await client.get("/v1/products/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/v1/products/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": "Bearer invalid-key"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "invalid_api_key"


@pytest.mark.asyncio
async def test_auth_valid_token(client: AsyncClient, db_session: AsyncSession):
    raw_key = "sk-agent-testkey123"
    await create_test_api_key(db_session, raw_key)

    # Valid token reaches the endpoint (404 is fine — product doesn't exist)
    resp = await client.get(
        "/v1/products/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_auth_inactive_key(client: AsyncClient, db_session: AsyncSession):
    raw_key = "sk-agent-inactivekey"
    api_key = APIKey(
        key_hash=hash_api_key(raw_key),
        name="inactive",
        owner_email="test@example.com",
        policy={},
        is_active=False,
    )
    db_session.add(api_key)
    await db_session.commit()

    resp = await client.get(
        "/v1/products/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 401
