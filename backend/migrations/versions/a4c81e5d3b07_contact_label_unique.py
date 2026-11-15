"""contact label and unique contacts

Revision ID: a4c81e5d3b07
Revises: 9ed7bf9d4225
Create Date: 2026-11-15 21:10:44.318207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a4c81e5d3b07'
down_revision: Union[str, Sequence[str], None] = '9ed7bf9d4225'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('authority_contacts', sa.Column('label', sa.String(length=300), nullable=True))
    op.create_unique_constraint(
        'uq_authority_contacts_authority_id',
        'authority_contacts',
        ['authority_id', 'type', 'value'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_authority_contacts_authority_id', 'authority_contacts', type_='unique')
    op.drop_column('authority_contacts', 'label')
