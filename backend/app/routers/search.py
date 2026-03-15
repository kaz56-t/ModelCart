from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import APIKey
from app.models.product import Product
from app.schemas.search import SearchRequest, SearchResponse
from app.services.auth import get_current_api_key

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_products(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    _api_key: APIKey = Depends(get_current_api_key),
) -> SearchResponse:
    query = select(Product)

    if body.keyword:
        like = f"%{body.keyword}%"
        query = query.where(
            Product.name.ilike(like) | Product.description.ilike(like)
        )
    if body.category is not None:
        query = query.where(Product.category == body.category)
    if body.min_price is not None:
        query = query.where(Product.price >= body.min_price)
    if body.max_price is not None:
        query = query.where(Product.price <= body.max_price)
    if body.in_stock is not None:
        query = query.where(Product.in_stock.is_(body.in_stock))
    if body.max_delivery_days is not None:
        query = query.where(Product.delivery_days <= body.max_delivery_days)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = count_result.scalar_one()

    result = await db.execute(query.offset(body.offset).limit(body.limit))
    items = list(result.scalars().all())

    if items:
        agent_hint = (
            f"{total}件の商品が見つかりました。"
            f"気になる商品は GET /v1/products/{{id}} で詳細を確認し、"
            f"POST /v1/orders で注文できます。"
        )
    else:
        agent_hint = (
            "条件に合う商品が見つかりませんでした。"
            "フィルター条件を緩めて再検索してください。"
        )

    return SearchResponse(
        items=items,
        total=total,
        limit=body.limit,
        offset=body.offset,
        agent_hint=agent_hint,
    )
