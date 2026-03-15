import uuid
from datetime import datetime

from sqlalchemy import Boolean, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_email: Mapped[str] = mapped_column(Text, nullable=False)
    policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    delivery_profiles: Mapped[list["DeliveryProfile"]] = relationship(  # noqa: F821
        back_populates="api_key", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(  # noqa: F821
        back_populates="api_key"
    )
    order_logs: Mapped[list["OrderLog"]] = relationship(  # noqa: F821
        back_populates="api_key"
    )
