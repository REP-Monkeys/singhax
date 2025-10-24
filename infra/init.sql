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

-- Create sample RAG documents for policy sections
INSERT INTO rag_documents (title, insurer_name, product_code, section_id, heading, text, citations, embedding) VALUES
('Comprehensive Travel Insurance', 'Demo Insurer', 'COMP_TRAVEL', '1.1', 'Coverage Overview', 'This policy provides comprehensive travel insurance coverage for medical expenses, trip cancellation, and baggage protection.', '{"section": "1.1", "page": 1}', '[0.1, 0.2, 0.3]'::vector),
('Comprehensive Travel Insurance', 'Demo Insurer', 'COMP_TRAVEL', '2.1', 'Medical Coverage', 'Medical expenses are covered up to $100,000 for emergency treatment during your trip.', '{"section": "2.1", "page": 5}', '[0.2, 0.3, 0.4]'::vector),
('Comprehensive Travel Insurance', 'Demo Insurer', 'COMP_TRAVEL', '3.1', 'Trip Cancellation', 'Trip cancellation coverage applies when you need to cancel your trip due to covered reasons such as illness or death.', '{"section": "3.1", "page": 10}', '[0.3, 0.4, 0.5]'::vector)
ON CONFLICT DO NOTHING;
