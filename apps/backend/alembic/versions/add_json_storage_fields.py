"""add_json_storage_fields

Revision ID: a1b2c3d4e5f6
Revises: 8d7e71b2d2f0
Create Date: 2025-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8d7e71b2d2f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add JSONB columns to quotes table
    op.add_column('quotes', sa.Column('ancileo_quotation_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('quotes', sa.Column('ancileo_purchase_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add JSONB column to trips table
    op.add_column('trips', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove columns from trips table
    op.drop_column('trips', 'metadata_json')
    
    # Remove columns from quotes table
    op.drop_column('quotes', 'ancileo_purchase_json')
    op.drop_column('quotes', 'ancileo_quotation_json')

