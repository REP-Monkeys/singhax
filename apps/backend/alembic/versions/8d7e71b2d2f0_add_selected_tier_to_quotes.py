"""add_selected_tier_to_quotes

Revision ID: 8d7e71b2d2f0
Revises: f1a2b3c4d5e6
Create Date: 2025-11-01 14:56:03.646709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8d7e71b2d2f0'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop and recreate the tiertype enum type to ensure correct values
    op.execute("DROP TYPE IF EXISTS tiertype CASCADE")
    op.execute("CREATE TYPE tiertype AS ENUM ('standard', 'elite', 'premier')")
    op.add_column('quotes', sa.Column('selected_tier', sa.Enum('standard', 'elite', 'premier', name='tiertype', create_type=False), server_default=sa.text("'standard'::tiertype"), nullable=False))


def downgrade() -> None:
    op.drop_column('quotes', 'selected_tier')
    op.execute("DROP TYPE IF EXISTS tiertype")
