import hashlib

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import APIKey

bearer_scheme = HTTPBearer()


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    key_hash = hash_api_key(credentials.credentials)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_api_key",
                "agent_hint": "APIキーが無効です。有効なBearer tokenをAuthorizationヘッダーに設定してください。",
            },
        )

    from sqlalchemy import func

    api_key.last_used_at = func.now()
    await db.commit()

    return api_key
