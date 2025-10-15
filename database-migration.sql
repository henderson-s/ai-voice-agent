-- Remove scenario_type column from agent_configurations table
ALTER TABLE agent_configurations DROP COLUMN IF EXISTS scenario_type;

-- Verify the table structure
-- Run this to see the current structure:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'agent_configurations';
