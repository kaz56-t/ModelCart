import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    delivery_days: Mapped[int] = mapped_column(Integer, default=3)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
