"""add_order_status_and_item_notes

Revision ID: c1b2d3e4f5a6
Revises: 7a9c41bb2f01
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1b2d3e4f5a6'
down_revision: Union[str, None] = '7a9c41bb2f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ORDER_STATUS_VALUES = (
    'shipping',
    'awaiting_delivery',
    'completed',
    'cancelled',
    'returning',
)


def upgrade() -> None:
    order_status = sa.Enum(*ORDER_STATUS_VALUES, name='orderstatus')
    order_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'orders',
        sa.Column(
            'status',
            order_status,
            nullable=False,
            server_default='shipping',
        ),
    )
    op.alter_column('orders', 'status', server_default=None)
    op.add_column(
        'order_items',
        sa.Column('notes', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('order_items', 'notes')
    op.drop_column('orders', 'status')
    sa.Enum(name='orderstatus').drop(op.get_bind(), checkfirst=True)
