import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PolicySchema(BaseModel):
    auto_approve_under: int | None = Field(None, ge=0)
    allowed_categories: list[str] = Field(default_factory=list)
    max_orders_per_day: int | None = Field(None, ge=1)
    max_items_per_order: int | None = Field(None, ge=1)
    require_dry_run: bool = False


class APIKeyCreate(BaseModel):
    name: str
    owner_email: EmailStr
    policy: PolicySchema = Field(default_factory=PolicySchema)


class APIKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    owner_email: str
    policy: dict
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None


class APIKeyCreateResponse(APIKeyResponse):
    """Returned only on creation — includes the raw key (shown once)."""

    raw_key: str
