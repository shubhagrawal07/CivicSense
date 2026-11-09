"""synthetic flags

Revision ID: 9ed7bf9d4225
Revises: d27f6b3a91c4
Create Date: 2026-11-09 16:01:14.492453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9ed7bf9d4225'
down_revision: Union[str, Sequence[str], None] = 'd27f6b3a91c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('issues', sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('issues', 'is_synthetic')
    op.drop_column('reports', 'is_synthetic')
