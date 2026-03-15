"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("in_stock", sa.Boolean(), server_default=sa.true()),
        sa.Column("stock_qty", sa.Integer(), server_default="0"),
        sa.Column("delivery_days", sa.Integer(), server_default="3"),
        sa.Column("attributes", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_products_category", "products", ["category"])
    op.create_index("idx_products_price", "products", ["price"])
    op.create_index("idx_products_delivery_days", "products", ["delivery_days"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key_hash", sa.Text(), unique=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("owner_email", sa.Text(), nullable=False),
        sa.Column("policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "delivery_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("postal_code", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.false()),
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False, server_default="confirmed"),
        sa.Column("items", postgresql.JSONB(), nullable=False),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("delivery_profile", postgresql.JSONB(), nullable=False),
        sa.Column("estimated_delivery", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_orders_api_key", "orders", ["api_key_id"])

    op.create_table(
        "order_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id"),
            nullable=False,
        ),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("request", postgresql.JSONB(), nullable=True),
        sa.Column("response", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_order_logs_api_key", "order_logs", ["api_key_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("order_logs")
    op.drop_table("orders")
    op.drop_table("delivery_profiles")
    op.drop_table("api_keys")
    op.drop_table("products")
