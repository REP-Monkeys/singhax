"""add_document_tables_with_file_storage

Revision ID: xxxx_add_doc_tables
Revises: ab6c277e7fb3
Create Date: 2025-11-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'xxxx_add_doc_tables'
down_revision: Union[str, None] = 'ab6c277e7fb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create flights table
    op.create_table('flights',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('source_filename', sa.String(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('json_file_path', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_content_type', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('airline_name', sa.String(), nullable=True),
        sa.Column('airline_code', sa.String(), nullable=True),
        sa.Column('departure_date', sa.Date(), nullable=True),
        sa.Column('departure_time', sa.String(), nullable=True),
        sa.Column('departure_airport_code', sa.String(), nullable=True),
        sa.Column('departure_airport_name', sa.String(), nullable=True),
        sa.Column('return_date', sa.Date(), nullable=True),
        sa.Column('return_time', sa.String(), nullable=True),
        sa.Column('return_airport_code', sa.String(), nullable=True),
        sa.Column('return_airport_name', sa.String(), nullable=True),
        sa.Column('flight_number_outbound', sa.String(), nullable=True),
        sa.Column('flight_number_inbound', sa.String(), nullable=True),
        sa.Column('destination_country', sa.String(), nullable=True),
        sa.Column('destination_city', sa.String(), nullable=True),
        sa.Column('destination_airport_code', sa.String(), nullable=True),
        sa.Column('pnr', sa.String(), nullable=True),
        sa.Column('booking_number', sa.String(), nullable=True),
        sa.Column('trip_duration_days', sa.Integer(), nullable=True),
        sa.Column('total_cost_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total_cost_currency', sa.String(length=3), nullable=True),
        sa.Column('travelers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_flights_user_id', 'flights', ['user_id'])
    op.create_index('idx_flights_session_id', 'flights', ['session_id'])
    op.create_index('idx_flights_departure_date', 'flights', ['departure_date'])
    
    # Create hotels table
    op.create_table('hotels',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('source_filename', sa.String(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('json_file_path', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_content_type', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('hotel_name', sa.String(), nullable=True),
        sa.Column('hotel_chain', sa.String(), nullable=True),
        sa.Column('star_rating', sa.Integer(), nullable=True),
        sa.Column('address_street', sa.String(), nullable=True),
        sa.Column('address_city', sa.String(), nullable=True),
        sa.Column('address_country', sa.String(), nullable=True),
        sa.Column('address_postal_code', sa.String(), nullable=True),
        sa.Column('address_full', sa.String(), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('check_in_date', sa.Date(), nullable=True),
        sa.Column('check_in_time', sa.String(), nullable=True),
        sa.Column('check_out_date', sa.Date(), nullable=True),
        sa.Column('check_out_time', sa.String(), nullable=True),
        sa.Column('nights_count', sa.Integer(), nullable=True),
        sa.Column('room_type', sa.String(), nullable=True),
        sa.Column('number_of_rooms', sa.Integer(), nullable=True),
        sa.Column('occupancy', sa.Integer(), nullable=True),
        sa.Column('smoking_preference', sa.String(), nullable=True),
        sa.Column('total_cost_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total_cost_currency', sa.String(length=3), nullable=True),
        sa.Column('per_night_cost_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('per_night_cost_currency', sa.String(length=3), nullable=True),
        sa.Column('deposit_paid_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('deposit_paid_currency', sa.String(length=3), nullable=True),
        sa.Column('is_refundable', sa.Boolean(), nullable=True),
        sa.Column('cancellation_policy', sa.Text(), nullable=True),
        sa.Column('confirmation_number', sa.String(), nullable=True),
        sa.Column('booking_id', sa.String(), nullable=True),
        sa.Column('guests', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_hotels_user_id', 'hotels', ['user_id'])
    op.create_index('idx_hotels_session_id', 'hotels', ['session_id'])
    op.create_index('idx_hotels_check_in_date', 'hotels', ['check_in_date'])
    
    # Create visas table
    op.create_table('visas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('source_filename', sa.String(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('json_file_path', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_content_type', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('visa_type', sa.String(), nullable=True),
        sa.Column('destination_country', sa.String(), nullable=True),
        sa.Column('entry_type', sa.String(), nullable=True),
        sa.Column('validity_start_date', sa.Date(), nullable=True),
        sa.Column('validity_end_date', sa.Date(), nullable=True),
        sa.Column('applicant_first_name', sa.String(), nullable=True),
        sa.Column('applicant_last_name', sa.String(), nullable=True),
        sa.Column('applicant_full_name', sa.String(), nullable=True),
        sa.Column('applicant_date_of_birth', sa.Date(), nullable=True),
        sa.Column('applicant_age', sa.Integer(), nullable=True),
        sa.Column('applicant_passport_number', sa.String(), nullable=True),
        sa.Column('applicant_nationality', sa.String(), nullable=True),
        sa.Column('trip_purpose_primary', sa.String(), nullable=True),
        sa.Column('trip_purpose_detailed', sa.Text(), nullable=True),
        sa.Column('is_business', sa.Boolean(), nullable=True),
        sa.Column('is_medical_treatment', sa.Boolean(), nullable=True),
        sa.Column('intended_arrival_date', sa.Date(), nullable=True),
        sa.Column('intended_departure_date', sa.Date(), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('destination_cities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('has_hotel_booking', sa.Boolean(), nullable=True),
        sa.Column('hotel_name', sa.String(), nullable=True),
        sa.Column('hotel_address', sa.String(), nullable=True),
        sa.Column('has_sufficient_funds', sa.Boolean(), nullable=True),
        sa.Column('estimated_trip_cost_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('estimated_trip_cost_currency', sa.String(length=3), nullable=True),
        sa.Column('has_previous_travel', sa.Boolean(), nullable=True),
        sa.Column('previous_destinations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_visas_user_id', 'visas', ['user_id'])
    op.create_index('idx_visas_session_id', 'visas', ['session_id'])
    op.create_index('idx_visas_destination_country', 'visas', ['destination_country'])
    
    # Create itineraries table
    op.create_table('itineraries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('source_filename', sa.String(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('json_file_path', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_content_type', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('trip_title', sa.String(), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('destinations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('activities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('has_adventure_sports', sa.Boolean(), nullable=True),
        sa.Column('adventure_sports_activities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('has_extreme_sports', sa.Boolean(), nullable=True),
        sa.Column('has_water_sports', sa.Boolean(), nullable=True),
        sa.Column('has_winter_sports', sa.Boolean(), nullable=True),
        sa.Column('has_high_altitude_activities', sa.Boolean(), nullable=True),
        sa.Column('has_motorized_sports', sa.Boolean(), nullable=True),
        sa.Column('is_group_travel', sa.Boolean(), nullable=True),
        sa.Column('has_remote_locations', sa.Boolean(), nullable=True),
        sa.Column('has_political_risk_destinations', sa.Boolean(), nullable=True),
        sa.Column('is_group_tour', sa.Boolean(), nullable=True),
        sa.Column('is_solo_travel', sa.Boolean(), nullable=True),
        sa.Column('group_size', sa.Integer(), nullable=True),
        sa.Column('includes_children', sa.Boolean(), nullable=True),
        sa.Column('includes_seniors', sa.Boolean(), nullable=True),
        sa.Column('trip_type', sa.String(), nullable=True),
        sa.Column('number_of_destinations', sa.Integer(), nullable=True),
        sa.Column('requires_internal_travel', sa.Boolean(), nullable=True),
        sa.Column('internal_transport', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('travelers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_itineraries_user_id', 'itineraries', ['user_id'])
    op.create_index('idx_itineraries_session_id', 'itineraries', ['session_id'])
    op.create_index('idx_itineraries_start_date', 'itineraries', ['start_date'])
    op.create_index('idx_itineraries_has_adventure_sports', 'itineraries', ['has_adventure_sports'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_itineraries_has_adventure_sports', table_name='itineraries')
    op.drop_index('idx_itineraries_start_date', table_name='itineraries')
    op.drop_index('idx_itineraries_session_id', table_name='itineraries')
    op.drop_index('idx_itineraries_user_id', table_name='itineraries')
    op.drop_table('itineraries')
    
    op.drop_index('idx_visas_destination_country', table_name='visas')
    op.drop_index('idx_visas_session_id', table_name='visas')
    op.drop_index('idx_visas_user_id', table_name='visas')
    op.drop_table('visas')
    
    op.drop_index('idx_hotels_check_in_date', table_name='hotels')
    op.drop_index('idx_hotels_session_id', table_name='hotels')
    op.drop_index('idx_hotels_user_id', table_name='hotels')
    op.drop_table('hotels')
    
    op.drop_index('idx_flights_departure_date', table_name='flights')
    op.drop_index('idx_flights_session_id', table_name='flights')
    op.drop_index('idx_flights_user_id', table_name='flights')
    op.drop_table('flights')

