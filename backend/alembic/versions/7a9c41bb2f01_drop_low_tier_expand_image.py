"""drop_low_tier_expand_image

Revision ID: 7a9c41bb2f01
Revises: 39da058fa6a3
Create Date: 2026-04-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7a9c41bb2f01'
down_revision: Union[str, None] = '39da058fa6a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('products', 'low_tier')
    op.alter_column(
        'products',
        'image',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'products',
        'image',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.add_column(
        'products',
        sa.Column('low_tier', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('products', 'low_tier', server_default=None)
