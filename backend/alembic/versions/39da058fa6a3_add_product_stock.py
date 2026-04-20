"""add_product_stock

Revision ID: 39da058fa6a3
Revises: 20dbff321163
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '39da058fa6a3'
down_revision: Union[str, None] = '20dbff321163'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column('stock', sa.Integer(), nullable=False, server_default='100'),
    )
    op.alter_column('products', 'stock', server_default=None)


def downgrade() -> None:
    op.drop_column('products', 'stock')
