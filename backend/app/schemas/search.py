from pydantic import BaseModel, Field

from app.schemas.products import ProductResponse


class SearchRequest(BaseModel):
    keyword: str | None = Field(None, description="Search in name and description")
    category: str | None = Field(None, description="Filter by category")
    min_price: int | None = Field(None, ge=0, description="Minimum price (JPY)")
    max_price: int | None = Field(None, ge=0, description="Maximum price (JPY)")
    in_stock: bool | None = Field(None, description="Filter by stock availability")
    max_delivery_days: int | None = Field(None, ge=0, description="Max delivery days")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SearchResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    limit: int
    offset: int
    agent_hint: str
