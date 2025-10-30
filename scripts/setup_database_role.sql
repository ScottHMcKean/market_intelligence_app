-- Script to create PostgreSQL role for Databricks App service principal
-- 
-- When a Databricks App connects to Lakebase, it uses its service principal ID
-- as the database username. This role must exist in PostgreSQL.
--
-- How to use this script:
-- 1. Get the UUID from your error message:
--    "FATAL: role "YOUR-UUID-HERE" does not exist"
-- 2. Replace YOUR-UUID-HERE below with that UUID
-- 3. Connect to your Lakebase instance
-- 4. Run this script

-- Replace this with your actual service principal UUID from the error message
-- Example: 2ab35418-2e68-42a1-8911-957f8ea7b1a0
\set role_name 'YOUR-UUID-HERE'

-- Create the role with LOGIN privilege
CREATE ROLE :role_name LOGIN;

-- Grant database connection
GRANT CONNECT ON DATABASE databricks_postgres TO :role_name;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO :role_name;

-- Grant table privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO :role_name;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO :role_name;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO :role_name;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO :role_name;

-- Verify the role was created
SELECT rolname, rolcanlogin, rolconnlimit 
FROM pg_roles 
WHERE rolname = :role_name;

-- Show granted privileges
\dp

