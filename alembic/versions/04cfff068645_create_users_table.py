"""create users table

Revision ID: 04cfff068645
Revises: e7242895bbf3
Create Date: 2026-06-02 17:55:20.643127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04cfff068645'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
