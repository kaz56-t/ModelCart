import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: int = Field(..., gt=0, description="Price in JPY (tax-excluded)")
    category: str
    in_stock: bool = True
    stock_qty: int = Field(default=0, ge=0)
    delivery_days: int = Field(default=3, ge=0)
    attributes: dict = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = Field(default=None, gt=0)
    category: str | None = None
    in_stock: bool | None = None
    stock_qty: int | None = Field(default=None, ge=0)
    delivery_days: int | None = Field(default=None, ge=0)
    attributes: dict | None = None


class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: str | None
    price: int
    category: str
    in_stock: bool
    stock_qty: int
    delivery_days: int
    attributes: dict
    created_at: datetime
    updated_at: datetime
