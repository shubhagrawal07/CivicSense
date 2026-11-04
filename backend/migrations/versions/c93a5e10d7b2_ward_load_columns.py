"""ward load columns

Revision ID: c93a5e10d7b2
Revises: b7d41c9a3e20
Create Date: 2026-11-04 10:15:42.118305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c93a5e10d7b2'
down_revision: Union[str, Sequence[str], None] = 'b7d41c9a3e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jurisdictions', sa.Column('osm_id', sa.BigInteger(), nullable=True))
    op.add_column('jurisdictions', sa.Column('ward_code', sa.String(length=50), nullable=True))
    op.create_unique_constraint('uq_jurisdictions_osm_id', 'jurisdictions', ['osm_id'])
    op.add_column('scrape_runs', sa.Column('summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('scrape_runs', 'summary')
    op.drop_constraint('uq_jurisdictions_osm_id', 'jurisdictions', type_='unique')
    op.drop_column('jurisdictions', 'ward_code')
    op.drop_column('jurisdictions', 'osm_id')
