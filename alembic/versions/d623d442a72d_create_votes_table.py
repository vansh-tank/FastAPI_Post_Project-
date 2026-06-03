"""create votes table

Revision ID: d623d442a72d
Revises: 04cfff068645
Create Date: 2026-06-02 17:56:10.000078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd623d442a72d'
down_revision: Union[str, Sequence[str], None] = '04cfff068645'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'votes',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('votes')
