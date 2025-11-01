-- Add JSONB columns for JSON storage structures
-- Run this script directly on your Supabase database

-- Add columns to quotes table
ALTER TABLE quotes 
ADD COLUMN IF NOT EXISTS ancileo_quotation_json JSONB,
ADD COLUMN IF NOT EXISTS ancileo_purchase_json JSONB;

-- Add column to trips table
ALTER TABLE trips 
ADD COLUMN IF NOT EXISTS metadata_json JSONB;

-- Verify columns were added
SELECT 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name IN ('quotes', 'trips') 
    AND column_name IN ('ancileo_quotation_json', 'ancileo_purchase_json', 'metadata_json')
ORDER BY table_name, column_name;

