"""scrape_runs pages_failed

Revision ID: c3a8e5d17f42
Revises: b7d41c9a3e20
Create Date: 2026-11-05 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3a8e5d17f42'
down_revision: Union[str, Sequence[str], None] = 'b7d41c9a3e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scrape_runs', sa.Column('pages_failed', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('scrape_runs', 'pages_failed')
