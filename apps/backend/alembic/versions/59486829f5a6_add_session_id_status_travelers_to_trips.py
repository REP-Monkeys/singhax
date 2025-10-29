"""add_session_id_status_travelers_to_trips

Revision ID: 59486829f5a6
Revises: e99c34b6bfdd
Create Date: 2025-10-29 12:03:53.957128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59486829f5a6'
down_revision: Union[str, None] = 'e99c34b6bfdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to trips table
    op.add_column('trips', sa.Column('session_id', sa.String(), nullable=True))
    op.add_column('trips', sa.Column('status', sa.String(), nullable=False, server_default='draft'))
    op.add_column('trips', sa.Column('travelers_count', sa.Integer(), nullable=False, server_default='1'))

    # Make start_date and end_date nullable for draft trips
    op.alter_column('trips', 'start_date', nullable=True)
    op.alter_column('trips', 'end_date', nullable=True)

    # Make destinations nullable
    op.alter_column('trips', 'destinations', nullable=True)

    # Create index on session_id for faster lookups
    op.create_index('ix_trips_session_id', 'trips', ['session_id'], unique=True)


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_trips_session_id', 'trips')

    # Revert columns to NOT NULL
    op.alter_column('trips', 'destinations', nullable=False)
    op.alter_column('trips', 'end_date', nullable=False)
    op.alter_column('trips', 'start_date', nullable=False)

    # Drop new columns
    op.drop_column('trips', 'travelers_count')
    op.drop_column('trips', 'status')
    op.drop_column('trips', 'session_id')
