import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="confirmed")
    items: Mapped[list] = mapped_column(JSONB, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_profile: Mapped[dict] = mapped_column(JSONB, nullable=False)
    estimated_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    api_key: Mapped["APIKey"] = relationship(back_populates="orders")  # noqa: F821
