-- Initialize notification service database
-- This script runs when PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create basic tables (will be managed by migrations later)
-- This is just to ensure database is ready

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE notification_service TO postgres;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Notification service database initialized successfully';
END $$;