import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import APIKey
from app.schemas.api_keys import APIKeyCreate, APIKeyCreateResponse, APIKeyResponse
from app.services.auth import generate_api_key

router = APIRouter(tags=["api-keys"])


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=201)
async def create_api_key(
    body: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreateResponse:
    raw_key, key_hash = generate_api_key()

    api_key = APIKey(
        key_hash=key_hash,
        name=body.name,
        owner_email=body.owner_email,
        policy=body.policy.model_dump(),
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        owner_email=api_key.owner_email,
        policy=api_key.policy,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        key=raw_key,
        agent_hint=(
            "APIキーを安全な場所に保存してください。このキーは一度しか表示されません。"
            " 以降のリクエストでは Authorization: Bearer <key> ヘッダーを使用してください。"
        ),
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
) -> list[APIKey]:
    result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    return list(result.scalars().all())


@router.delete("/api-keys/{api_key_id}", status_code=204)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    api_key.is_active = False
    await db.commit()
