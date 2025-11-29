-- Initialize PGVector extension for df_healthbench database
-- This script is automatically executed when the PostgreSQL container starts
-- (only on first initialization when the database is created)

-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE 'PGVector extension successfully enabled';
    ELSE
        RAISE EXCEPTION 'Failed to enable PGVector extension';
    END IF;
END $$;

