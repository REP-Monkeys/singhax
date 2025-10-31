"""add_payments_table

Revision ID: ab6c277e7fb3
Revises: 59486829f5a6
Create Date: 2025-10-31 21:13:56.635197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ab6c277e7fb3'
down_revision: Union[str, None] = '59486829f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if payments table already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    if 'payments' in existing_tables:
        print("Payments table already exists, skipping creation")
        # Mark migration as applied
        return
    
    # Create payment status enum (if it doesn't exist)
    # Use raw SQL to handle the enum creation
    connection.execute(sa.text("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymentstatus') THEN
                CREATE TYPE paymentstatus AS ENUM ('pending', 'completed', 'failed', 'expired');
            END IF;
        END $$;
    """))
    
    # Create payments table
    # Use String instead of Enum to avoid SQLAlchemy trying to create the enum
    # We'll cast it properly in the model
    op.create_table('payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('quote_id', sa.UUID(), nullable=False),
        sa.Column('payment_intent_id', sa.String(), nullable=False),
        sa.Column('stripe_session_id', sa.String(), nullable=True),
        sa.Column('stripe_payment_intent', sa.String(), nullable=True),
        sa.Column('payment_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('product_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('webhook_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_intent_id')
    )
    
    # Create indexes
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_quote_id', 'payments', ['quote_id'])
    op.create_index('ix_payments_payment_intent_id', 'payments', ['payment_intent_id'])
    op.create_index('ix_payments_stripe_session_id', 'payments', ['stripe_session_id'])
    
    # Alter payment_status column to use enum type (after table creation)
    # First drop the default, then alter type, then set default
    op.execute("ALTER TABLE payments ALTER COLUMN payment_status DROP DEFAULT")
    op.execute("ALTER TABLE payments ALTER COLUMN payment_status TYPE paymentstatus USING payment_status::paymentstatus")
    op.execute("ALTER TABLE payments ALTER COLUMN payment_status SET DEFAULT 'pending'::paymentstatus")


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_payments_stripe_session_id', table_name='payments')
    op.drop_index('ix_payments_payment_intent_id', table_name='payments')
    op.drop_index('ix_payments_quote_id', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    
    # Drop table
    op.drop_table('payments')
    
    # Drop enum
    op.execute("DROP TYPE paymentstatus")
