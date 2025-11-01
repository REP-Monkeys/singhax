"""add_trip_type_and_airline_fields_to_flights

Revision ID: f1a2b3c4d5e6
Revises: xxxx_add_doc_tables
Create Date: 2025-11-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'xxxx_add_doc_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add trip_type column
    op.add_column('flights', sa.Column('trip_type', sa.String(), nullable=True))
    
    # Add outbound airline columns
    op.add_column('flights', sa.Column('outbound_airline_name', sa.String(), nullable=True))
    op.add_column('flights', sa.Column('outbound_airline_code', sa.String(), nullable=True))
    
    # Add inbound airline columns
    op.add_column('flights', sa.Column('inbound_airline_name', sa.String(), nullable=True))
    op.add_column('flights', sa.Column('inbound_airline_code', sa.String(), nullable=True))
    
    # Update existing records: infer trip_type from return_date
    # Set trip_type to 'return' if return_date exists, otherwise 'one_way'
    op.execute("""
        UPDATE flights 
        SET trip_type = CASE 
            WHEN return_date IS NOT NULL THEN 'return'
            ELSE 'one_way'
        END
    """)
    
    # For existing records, populate outbound/inbound airlines from airline_name/airline_code
    # If return_date exists, set both outbound and inbound to the same airline
    # Otherwise, set only outbound
    op.execute("""
        UPDATE flights 
        SET 
            outbound_airline_name = airline_name,
            outbound_airline_code = airline_code,
            inbound_airline_name = CASE 
                WHEN return_date IS NOT NULL THEN airline_name
                ELSE NULL
            END,
            inbound_airline_code = CASE 
                WHEN return_date IS NOT NULL THEN airline_code
                ELSE NULL
            END
    """)


def downgrade() -> None:
    # Drop new columns
    op.drop_column('flights', 'inbound_airline_code')
    op.drop_column('flights', 'inbound_airline_name')
    op.drop_column('flights', 'outbound_airline_code')
    op.drop_column('flights', 'outbound_airline_name')
    op.drop_column('flights', 'trip_type')

