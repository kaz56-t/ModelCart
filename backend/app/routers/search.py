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
    api_key: APIKey = Depends(get_current_api_key),
) -> SearchResponse:
    query = select(Product)

    if body.category is not None:
        query = query.where(Product.category == body.category)
    if body.max_price is not None:
        query = query.where(Product.price <= body.max_price)
    if body.max_delivery_days is not None:
        query = query.where(Product.delivery_days <= body.max_delivery_days)
    if body.in_stock_only:
        query = query.where(Product.in_stock == True)  # noqa: E712

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(Product.created_at.desc()).offset(body.offset).limit(body.limit)
    result = await db.execute(query)
    products = list(result.scalars().all())

    if total == 0:
        agent_hint = "検索結果が0件です。フィルター条件を緩めて再試行してください。例: in_stock_only=false, max_priceを上げる。"
    elif body.offset + body.limit < total:
        next_offset = body.offset + body.limit
        agent_hint = (
            f"全{total}件中{body.offset + 1}〜{body.offset + len(products)}件を表示。"
            f"次のページを取得するには offset={next_offset} を指定してください。"
        )
    else:
        agent_hint = (
            f"全{total}件の検索結果をすべて表示しました。"
            " 注文するには POST /v1/orders を使用してください。"
        )

    return SearchResponse(
        products=products,
        total=total,
        limit=body.limit,
        offset=body.offset,
        agent_hint=agent_hint,
    )
