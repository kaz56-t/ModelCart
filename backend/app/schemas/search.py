from pydantic import BaseModel, Field

from app.schemas.products import ProductResponse


class SearchRequest(BaseModel):
    category: str | None = None
    max_price: int | None = Field(default=None, gt=0)
    max_delivery_days: int | None = Field(default=None, ge=0)
    in_stock_only: bool = True
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)


class SearchResponse(BaseModel):
    products: list[ProductResponse]
    total: int
    limit: int
    offset: int
    agent_hint: str
