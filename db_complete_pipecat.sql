-- ============================================
-- AI Voice Agent - Complete Database Schema
-- Pipecat Migration Edition
-- ============================================
-- This is a complete, clean schema for the Pipecat-based
-- voice agent system. Run this on a fresh database or
-- after dropping existing tables.
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. DROP EXISTING TABLES (if re-running)
-- ============================================
-- Uncomment these if you want to start fresh
-- DROP TABLE IF EXISTS call_analytics CASCADE;
-- DROP TABLE IF EXISTS analytics_events CASCADE;
-- DROP TABLE IF EXISTS call_results CASCADE;
-- DROP TABLE IF EXISTS call_transcripts CASCADE;
-- DROP TABLE IF EXISTS calls CASCADE;
-- DROP TABLE IF EXISTS agent_configurations CASCADE;

-- ============================================
-- 2. AGENT CONFIGURATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS agent_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Basic Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scenario_type VARCHAR(50) DEFAULT 'driver_checkin' CHECK (scenario_type IN ('driver_checkin', 'emergency_protocol')),

    -- AI Configuration
    system_prompt TEXT NOT NULL,
    initial_greeting TEXT NOT NULL,

    -- Legacy Retell AI IDs (nullable for Pipecat migration)
    retell_agent_id VARCHAR(255) DEFAULT NULL,
    retell_llm_id VARCHAR(255) DEFAULT NULL,

    -- Pipecat AI Provider Configuration
    llm_provider VARCHAR(50) DEFAULT 'openai',
    llm_model VARCHAR(100) DEFAULT 'gpt-4',
    tts_provider VARCHAR(50) DEFAULT 'cartesia',
    tts_voice_id VARCHAR(100) DEFAULT 'sonic-english',
    stt_provider VARCHAR(50) DEFAULT 'deepgram',
    pipecat_config JSONB DEFAULT '{}',

    -- Voice Settings
    voice_id VARCHAR(100) DEFAULT '11labs-Adrian',
    language VARCHAR(10) DEFAULT 'en-US',

    -- Advanced Human-like Settings
    enable_backchannel BOOLEAN DEFAULT true,
    backchannel_words TEXT[] DEFAULT ARRAY['mm-hmm', 'I see', 'got it', 'okay'],
    enable_filler_words BOOLEAN DEFAULT true,
    filler_words TEXT[] DEFAULT ARRAY['um', 'uh', 'hmm', 'let me see'],

    -- Conversation Dynamics
    interruption_sensitivity DECIMAL(3,2) DEFAULT 0.7 CHECK (interruption_sensitivity BETWEEN 0 AND 1),
    response_delay_ms INTEGER DEFAULT 800,
    responsiveness DECIMAL(3,2) DEFAULT 0.8 CHECK (responsiveness BETWEEN 0 AND 1),

    -- Ambient Sound
    ambient_sound VARCHAR(50) DEFAULT 'call-center' CHECK (ambient_sound IN ('call-center', 'coffee-shop', 'convention-hall', 'summer-outdoor', 'mountain-outdoor', 'static-noise', 'off')),
    ambient_sound_volume DECIMAL(3,2) DEFAULT 0.5 CHECK (ambient_sound_volume BETWEEN 0 AND 2),

    -- Call Duration Settings
    max_call_duration_seconds INTEGER DEFAULT 600,
    enable_auto_end_call BOOLEAN DEFAULT true,
    end_call_after_silence_ms INTEGER DEFAULT 10000,

    -- Pronunciation & Keywords
    pronunciation_guide JSONB DEFAULT '{}',
    reminder_keywords TEXT[] DEFAULT ARRAY['POD', 'proof of delivery', 'paperwork'],
    enable_reminder BOOLEAN DEFAULT true,
    emergency_keywords TEXT[] DEFAULT ARRAY['accident', 'crash', 'emergency', 'help', 'breakdown', 'broke down', 'medical', 'injury', 'blowout', 'flat tire', 'broke', 'stuck'],

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for agent lookup
CREATE INDEX IF NOT EXISTS idx_agent_configurations_user_id ON agent_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_configurations_retell_agent_id ON agent_configurations(retell_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_configurations_llm_provider ON agent_configurations(llm_provider);
CREATE INDEX IF NOT EXISTS idx_agent_configurations_is_active ON agent_configurations(is_active);

-- ============================================
-- 3. CALLS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_configuration_id UUID REFERENCES agent_configurations(id) ON DELETE SET NULL,

    -- Call Info
    retell_call_id VARCHAR(255) UNIQUE,
    call_type VARCHAR(20) NOT NULL CHECK (call_type IN ('phone', 'web')),
    status VARCHAR(50) DEFAULT 'initiated' CHECK (status IN ('initiated', 'in_progress', 'completed', 'failed', 'ended')),

    -- Driver Info
    driver_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    load_number VARCHAR(100) NOT NULL,

    -- Call Metrics
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    recording_url TEXT,
    public_log_url TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for call lookup
CREATE INDEX IF NOT EXISTS idx_calls_user_id ON calls(user_id);
CREATE INDEX IF NOT EXISTS idx_calls_retell_call_id ON calls(retell_call_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent_configuration_id ON calls(agent_configuration_id);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at DESC);

-- ============================================
-- 4. CALL TRANSCRIPTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS call_transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,

    -- Transcript Data
    transcript TEXT NOT NULL,
    transcript_json JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure one transcript per call
    UNIQUE(call_id)
);

-- Index for transcript lookup
CREATE INDEX IF NOT EXISTS idx_call_transcripts_call_id ON call_transcripts(call_id);

-- ============================================
-- 5. CALL RESULTS TABLE (Structured Data Extraction)
-- ============================================
CREATE TABLE IF NOT EXISTS call_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,

    -- Scenario Info
    scenario_type VARCHAR(50) DEFAULT 'driver_checkin' CHECK (scenario_type IN ('driver_checkin', 'emergency_protocol')),
    is_emergency BOOLEAN DEFAULT false,

    -- Call Summary
    call_summary TEXT,
    call_outcome VARCHAR(100),

    -- Normal Check-in Fields (driver_checkin)
    driver_status VARCHAR(50),
    current_location TEXT,
    eta VARCHAR(100),
    delay_reason TEXT,
    unloading_status VARCHAR(100),
    dock_door VARCHAR(50),
    pod_reminder_acknowledged BOOLEAN,

    -- Emergency Fields (emergency_protocol)
    emergency_type VARCHAR(50),
    is_safe BOOLEAN,
    injuries VARCHAR(255),
    location_emergency TEXT,
    load_secure BOOLEAN,
    safety_status TEXT,
    injury_status VARCHAR(100),
    escalation_status VARCHAR(100),

    -- Raw Analysis Data
    analysis_data JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2),
    processing_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure one result per call
    UNIQUE(call_id)
);

-- Indexes for results lookup
CREATE INDEX IF NOT EXISTS idx_call_results_call_id ON call_results(call_id);
CREATE INDEX IF NOT EXISTS idx_call_results_scenario_type ON call_results(scenario_type);
CREATE INDEX IF NOT EXISTS idx_call_results_is_emergency ON call_results(is_emergency);

-- ============================================
-- 6. ANALYTICS EVENTS TABLE (Pipecat RTVI)
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    
    -- Event Info
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    
    -- Timestamp
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_analytics_events_call_id ON analytics_events(call_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp DESC);

-- ============================================
-- 7. CALL ANALYTICS TABLE (Aggregated Metrics)
-- ============================================
CREATE TABLE IF NOT EXISTS call_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    
    -- Call Metrics
    total_duration_ms INTEGER,
    interruption_count INTEGER DEFAULT 0,
    sentiment_shifts INTEGER DEFAULT 0,
    keywords_detected INTEGER DEFAULT 0,
    
    -- Token Usage
    tokens_spent INTEGER DEFAULT 0,
    
    -- Cost Tracking (in USD)
    llm_cost DECIMAL(10, 4) DEFAULT 0.0000,
    tts_cost DECIMAL(10, 4) DEFAULT 0.0000,
    stt_cost DECIMAL(10, 4) DEFAULT 0.0000,
    total_cost DECIMAL(10, 4) DEFAULT 0.0000,
    
    -- Additional Metrics (JSONB for flexibility)
    additional_metrics JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one analytics record per call
    UNIQUE(call_id)
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_call_analytics_call_id ON call_analytics(call_id);
CREATE INDEX IF NOT EXISTS idx_call_analytics_total_cost ON call_analytics(total_cost DESC);
CREATE INDEX IF NOT EXISTS idx_call_analytics_created_at ON call_analytics(created_at DESC);

-- ============================================
-- 8. TRIGGERS FOR UPDATED_AT
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables
DROP TRIGGER IF EXISTS update_agent_configurations_updated_at ON agent_configurations;
CREATE TRIGGER update_agent_configurations_updated_at
    BEFORE UPDATE ON agent_configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_calls_updated_at ON calls;
CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_call_transcripts_updated_at ON call_transcripts;
CREATE TRIGGER update_call_transcripts_updated_at
    BEFORE UPDATE ON call_transcripts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_call_results_updated_at ON call_results;
CREATE TRIGGER update_call_results_updated_at
    BEFORE UPDATE ON call_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_call_analytics_updated_at ON call_analytics;
CREATE TRIGGER update_call_analytics_updated_at
    BEFORE UPDATE ON call_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 9. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE agent_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_analytics ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Agent Configurations Policies
-- ============================================
DROP POLICY IF EXISTS "Users can view their own agent configurations" ON agent_configurations;
CREATE POLICY "Users can view their own agent configurations"
    ON agent_configurations FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create their own agent configurations" ON agent_configurations;
CREATE POLICY "Users can create their own agent configurations"
    ON agent_configurations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own agent configurations" ON agent_configurations;
CREATE POLICY "Users can update their own agent configurations"
    ON agent_configurations FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own agent configurations" ON agent_configurations;
CREATE POLICY "Users can delete their own agent configurations"
    ON agent_configurations FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- Calls Policies
-- ============================================
DROP POLICY IF EXISTS "Users can view their own calls" ON calls;
CREATE POLICY "Users can view their own calls"
    ON calls FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create their own calls" ON calls;
CREATE POLICY "Users can create their own calls"
    ON calls FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own calls" ON calls;
CREATE POLICY "Users can update their own calls"
    ON calls FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own calls" ON calls;
CREATE POLICY "Users can delete their own calls"
    ON calls FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- Call Transcripts Policies
-- ============================================
DROP POLICY IF EXISTS "Users can view transcripts of their own calls" ON call_transcripts;
CREATE POLICY "Users can view transcripts of their own calls"
    ON call_transcripts FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can create transcripts for their own calls" ON call_transcripts;
CREATE POLICY "Users can create transcripts for their own calls"
    ON call_transcripts FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can update transcripts of their own calls" ON call_transcripts;
CREATE POLICY "Users can update transcripts of their own calls"
    ON call_transcripts FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can delete transcripts of their own calls" ON call_transcripts;
CREATE POLICY "Users can delete transcripts of their own calls"
    ON call_transcripts FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

-- ============================================
-- Call Results Policies
-- ============================================
DROP POLICY IF EXISTS "Users can view results of their own calls" ON call_results;
CREATE POLICY "Users can view results of their own calls"
    ON call_results FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can create results for their own calls" ON call_results;
CREATE POLICY "Users can create results for their own calls"
    ON call_results FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can update results of their own calls" ON call_results;
CREATE POLICY "Users can update results of their own calls"
    ON call_results FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can delete results of their own calls" ON call_results;
CREATE POLICY "Users can delete results of their own calls"
    ON call_results FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

-- ============================================
-- Analytics Events Policies
-- ============================================
DROP POLICY IF EXISTS "Users can view events of their own calls" ON analytics_events;
CREATE POLICY "Users can view events of their own calls"
    ON analytics_events FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = analytics_events.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can create events for their own calls" ON analytics_events;
CREATE POLICY "Users can create events for their own calls"
    ON analytics_events FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = analytics_events.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can update events of their own calls" ON analytics_events;
CREATE POLICY "Users can update events of their own calls"
    ON analytics_events FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = analytics_events.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can delete events of their own calls" ON analytics_events;
CREATE POLICY "Users can delete events of their own calls"
    ON analytics_events FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = analytics_events.call_id
        AND calls.user_id = auth.uid()
    ));

-- ============================================
-- Call Analytics Policies
-- ============================================
DROP POLICY IF EXISTS "Users can view analytics of their own calls" ON call_analytics;
CREATE POLICY "Users can view analytics of their own calls"
    ON call_analytics FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_analytics.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can create analytics for their own calls" ON call_analytics;
CREATE POLICY "Users can create analytics for their own calls"
    ON call_analytics FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_analytics.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can update analytics of their own calls" ON call_analytics;
CREATE POLICY "Users can update analytics of their own calls"
    ON call_analytics FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_analytics.call_id
        AND calls.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can delete analytics of their own calls" ON call_analytics;
CREATE POLICY "Users can delete analytics of their own calls"
    ON call_analytics FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_analytics.call_id
        AND calls.user_id = auth.uid()
    ));

-- ============================================
-- 10. HELPFUL VIEWS
-- ============================================

-- View for call analytics with basic call info
CREATE OR REPLACE VIEW call_analytics_summary AS
SELECT 
    ca.*,
    c.user_id,
    c.driver_name,
    c.load_number,
    c.status,
    c.created_at as call_created_at,
    cr.call_outcome,
    cr.scenario_type
FROM call_analytics ca
JOIN calls c ON ca.call_id = c.id
LEFT JOIN call_results cr ON ca.call_id = cr.call_id;

-- View for event summary by call
CREATE OR REPLACE VIEW call_event_summary AS
SELECT 
    call_id,
    COUNT(*) as total_events,
    COUNT(DISTINCT event_type) as unique_event_types,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event
FROM analytics_events
GROUP BY call_id;

-- ============================================
-- 11. SERVICE ROLE BYPASS (For Webhooks & Background Jobs)
-- ============================================
-- Note: Service role key bypasses RLS automatically
-- No additional policies needed for service operations

-- ============================================
-- 12. TABLE COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE agent_configurations IS 'AI agent configurations with voice pipeline settings';
COMMENT ON TABLE calls IS 'Voice call records with metadata and status';
COMMENT ON TABLE call_transcripts IS 'Full conversation transcripts from voice calls';
COMMENT ON TABLE call_results IS 'Structured data extracted from call transcripts';
COMMENT ON TABLE analytics_events IS 'Real-time events captured during calls via RTVI observers';
COMMENT ON TABLE call_analytics IS 'Aggregated analytics metrics per call';

COMMENT ON COLUMN agent_configurations.retell_agent_id IS 'Legacy Retell AI agent ID - nullable for Pipecat';
COMMENT ON COLUMN agent_configurations.retell_llm_id IS 'Legacy Retell AI LLM ID - nullable for Pipecat';
COMMENT ON COLUMN agent_configurations.llm_provider IS 'LLM provider (openai, anthropic, etc.)';
COMMENT ON COLUMN agent_configurations.llm_model IS 'LLM model identifier (gpt-4, claude-3, etc.)';
COMMENT ON COLUMN agent_configurations.tts_provider IS 'Text-to-speech provider (cartesia, elevenlabs, etc.)';
COMMENT ON COLUMN agent_configurations.tts_voice_id IS 'TTS voice identifier';
COMMENT ON COLUMN agent_configurations.stt_provider IS 'Speech-to-text provider (deepgram, etc.)';
COMMENT ON COLUMN agent_configurations.pipecat_config IS 'Additional Pipecat-specific configuration';

-- ============================================
-- SCHEMA COMPLETE ✅
-- ============================================
-- Tables Created:
-- 1. agent_configurations (with Pipecat fields)
-- 2. calls
-- 3. call_transcripts
-- 4. call_results
-- 5. analytics_events (NEW for RTVI)
-- 6. call_analytics (NEW for metrics)
--
-- Features:
-- ✅ Pipecat-specific fields
-- ✅ Legacy Retell fields (nullable)
-- ✅ RTVI analytics tracking
-- ✅ Cost tracking per service
-- ✅ RLS policies for security
-- ✅ Optimized indexes
-- ✅ Automatic updated_at triggers
-- ✅ Helpful views
-- ✅ Documentation comments
-- ============================================

-- Verification Query
SELECT 
    'agent_configurations' as table_name,
    COUNT(*) as row_count
FROM agent_configurations
UNION ALL
SELECT 'calls', COUNT(*) FROM calls
UNION ALL
SELECT 'call_transcripts', COUNT(*) FROM call_transcripts
UNION ALL
SELECT 'call_results', COUNT(*) FROM call_results
UNION ALL
SELECT 'analytics_events', COUNT(*) FROM analytics_events
UNION ALL
SELECT 'call_analytics', COUNT(*) FROM call_analytics;

