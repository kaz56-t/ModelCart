import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OrderLog(Base):
    __tablename__ = "order_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    request: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    api_key: Mapped["APIKey"] = relationship(back_populates="order_logs")  # noqa: F821
