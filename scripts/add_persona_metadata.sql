-- Migration: Add metadata column to personas table
-- This adds a flexible JSON metadata field to support tagging, versioning, and other organizational schemes
-- Following the same pattern as analysis_configs.config which uses JSONB

BEGIN;

-- Add persona_metadata column to personas table (using JSONB like analysis_configs)
ALTER TABLE personas ADD COLUMN persona_metadata JSONB;

-- Add GIN index for persona_metadata queries to improve performance (following analysis_configs pattern)
CREATE INDEX idx_personas_persona_metadata ON personas USING GIN (persona_metadata);

-- Add comment to document the purpose of the persona_metadata field
COMMENT ON COLUMN personas.persona_metadata IS 'Flexible JSON metadata for tagging, versioning, and organizational schemes';

-- Verify the migration worked
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'personas' 
AND column_name = 'persona_metadata';

-- Show the updated table structure
\d personas

COMMIT;
