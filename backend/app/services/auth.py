import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.api_key import APIKey

bearer_scheme = HTTPBearer()


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Return (plaintext_key, key_hash)."""
    token = secrets.token_urlsafe(32)
    raw_key = f"{settings.API_KEY_PREFIX}{token}"
    return raw_key, hash_key(raw_key)


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    raw_key = credentials.credentials
    key_hash = hash_key(raw_key)

    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)  # noqa: E712
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "agent_hint": "APIキーが無効です。有効なBearer tokenをAuthorizationヘッダーに設定してください。",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_used_at without blocking
    from sqlalchemy import func

    api_key.last_used_at = func.now()
    await db.commit()

    return api_key
