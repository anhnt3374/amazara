"""add_chat_tables

Revision ID: d7e8f1a2b3c4
Revises: c1b2d3e4f5a6
Create Date: 2026-04-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd7e8f1a2b3c4'
down_revision: Union[str, None] = 'c1b2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONVERSATION_TYPE_VALUES = ('user_store', 'user_system')
SENDER_TYPE_VALUES = ('user', 'store', 'bot', 'system')
MESSAGE_REF_TYPE_VALUES = ('product', 'order', 'order_event')


def upgrade() -> None:
    conversation_type = sa.Enum(*CONVERSATION_TYPE_VALUES, name='conversationtype')
    sender_type = sa.Enum(*SENDER_TYPE_VALUES, name='sendertype')
    message_ref_type = sa.Enum(*MESSAGE_REF_TYPE_VALUES, name='messagereftype')

    conversation_type.create(op.get_bind(), checkfirst=True)
    sender_type.create(op.get_bind(), checkfirst=True)
    message_ref_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('type', conversation_type, nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('store_id', sa.String(length=36), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('last_read_at_user', sa.DateTime(), nullable=True),
        sa.Column('last_read_at_store', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'store_id', 'type', name='uq_conversation_pair'),
    )
    op.create_index('ix_conversation_user', 'conversations', ['user_id', 'last_message_at'])
    op.create_index('ix_conversation_store', 'conversations', ['store_id', 'last_message_at'])

    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('sender_type', sender_type, nullable=False),
        sa.Column('sender_id', sa.String(length=36), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('ref_type', message_ref_type, nullable=True),
        sa.Column('ref_id', sa.String(length=36), nullable=True),
        sa.Column('ref_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['conversation_id'], ['conversations.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_message_conversation_created',
        'messages',
        ['conversation_id', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_message_conversation_created', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_conversation_store', table_name='conversations')
    op.drop_index('ix_conversation_user', table_name='conversations')
    op.drop_table('conversations')
    sa.Enum(name='messagereftype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sendertype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='conversationtype').drop(op.get_bind(), checkfirst=True)
