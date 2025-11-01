"""add voice_transcripts table

Revision ID: voice_001
Revises: 8d7e71b2d2f0
Create Date: 2025-11-01 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'voice_001'
down_revision: Union[str, None] = '8d7e71b2d2f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create voice_transcripts table
    op.create_table(
        'voice_transcripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_audio_transcript', sa.Text(), nullable=False),
        sa.Column('ai_response_text', sa.Text(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )


def downgrade() -> None:
    # Drop voice_transcripts table
    op.drop_table('voice_transcripts')

