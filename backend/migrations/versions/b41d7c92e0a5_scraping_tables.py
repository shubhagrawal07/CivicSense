"""scraping tables

Revision ID: b41d7c92e0a5
Revises: eff889212e9e
Create Date: 2026-10-27 18:20:11.304512

"""
from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa


revision: str = 'b41d7c92e0a5'
down_revision: Union[str, Sequence[str], None] = 'eff889212e9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('jurisdictions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('authority_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('boundary', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
    sa.Column('source', sa.String(length=500), nullable=True),
    sa.Column('status', sa.Enum('CANDIDATE', 'APPROVED', name='jurisdiction_status'), nullable=False),
    sa.ForeignKeyConstraint(['authority_id'], ['authorities.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jurisdictions_authority_id'), 'jurisdictions', ['authority_id'], unique=False)
    op.create_table('authority_services',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('authority_id', sa.Integer(), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['authority_id'], ['authorities.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('authority_id', 'department_id')
    )
    op.create_table('scrape_runs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=200), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('RUNNING', 'SUCCEEDED', 'FAILED', name='scrape_status'), nullable=False),
    sa.Column('rows_added', sa.Integer(), server_default='0', nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('raw_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scrape_run_id', sa.Integer(), nullable=False),
    sa.Column('source_url', sa.String(length=1000), nullable=False),
    sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('content_type', sa.String(length=100), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['scrape_run_id'], ['scrape_runs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_documents_scrape_run_id'), 'raw_documents', ['scrape_run_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_raw_documents_scrape_run_id'), table_name='raw_documents')
    op.drop_table('raw_documents')
    op.drop_table('scrape_runs')
    op.drop_table('authority_services')
    op.drop_index(op.f('ix_jurisdictions_authority_id'), table_name='jurisdictions')
    op.drop_table('jurisdictions')
    op.execute("DROP TYPE IF EXISTS scrape_status")
    op.execute("DROP TYPE IF EXISTS jurisdiction_status")
