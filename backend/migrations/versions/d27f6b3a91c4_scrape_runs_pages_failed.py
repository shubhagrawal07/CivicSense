"""scrape runs pages failed

Revision ID: d27f6b3a91c4
Revises: c93a5e10d7b2
Create Date: 2026-11-07 11:42:09.552310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd27f6b3a91c4'
down_revision: Union[str, Sequence[str], None] = 'c93a5e10d7b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scrape_runs', sa.Column('pages_failed', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('scrape_runs', 'pages_failed')
