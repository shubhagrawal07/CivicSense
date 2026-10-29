"""report images

Revision ID: b7d41c9a3e20
Revises: eff889212e9e
Create Date: 2026-10-30 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7d41c9a3e20'
down_revision: Union[str, Sequence[str], None] = 'eff889212e9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('report_images',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('report_id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(length=500), nullable=False),
    sa.Column('position', sa.Integer(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_images_report_id'), 'report_images', ['report_id'], unique=False)
    op.execute(
        "INSERT INTO report_images (report_id, file_name, position) "
        "SELECT id, image_path, 0 FROM reports WHERE image_path IS NOT NULL"
    )
    op.drop_column('reports', 'image_path')


def downgrade() -> None:
    op.add_column('reports', sa.Column('image_path', sa.String(length=500), nullable=True))
    op.execute(
        "UPDATE reports SET image_path = ("
        "SELECT file_name FROM report_images "
        "WHERE report_images.report_id = reports.id "
        "ORDER BY position, id LIMIT 1)"
    )
    op.drop_index(op.f('ix_report_images_report_id'), table_name='report_images')
    op.drop_table('report_images')
