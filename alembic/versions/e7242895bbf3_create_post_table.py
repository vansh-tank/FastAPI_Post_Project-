"""create post table

Revision ID: e7242895bbf3
Revises: 
Create Date: 2026-06-02 17:40:06.030374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7242895bbf3'
down_revision: Union[str, Sequence[str], None] = '04cfff068645'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('published', sa.Boolean, server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    )
    


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('posts')
