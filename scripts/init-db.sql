-- Initialize notification service database
-- This script runs when PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tables will be managed by Tortoise ORM and Aerich migrations
-- This script just prepares the database environment

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE notification_service TO postgres;

-- Create schema for Aerich migrations
CREATE SCHEMA IF NOT EXISTS public;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Notification service database initialized for Tortoise ORM';
END $$;