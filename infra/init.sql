-- Initialize PostgreSQL database with pgvector extension
-- This script runs when the database container starts

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the main database (if not exists)
-- Note: The database is created by the POSTGRES_DB environment variable

-- Create any additional schemas or initial data here
-- This is where you would add seed data, initial users, etc.

-- Example: Create a sample user (for development only)
-- INSERT INTO users (email, name, hashed_password) 
-- VALUES ('demo@example.com', 'Demo User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4U.8F7hB2u')
-- ON CONFLICT (email) DO NOTHING;

-- Sample data will be loaded via database migrations and seed scripts
-- This ensures tables exist before inserting data
