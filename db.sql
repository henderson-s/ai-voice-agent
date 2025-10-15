-- ============================================
-- AI Voice Agent Database Schema
-- Supabase / PostgreSQL
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. USERS TABLE (Supabase Auth Integration)
-- ============================================
-- Note: This table is managed by Supabase Auth
-- Users are created via Supabase authentication
-- Reference: auth.users table

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

    -- Retell AI IDs
    retell_agent_id VARCHAR(255),
    retell_llm_id VARCHAR(255),

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

-- Index for user lookup
CREATE INDEX IF NOT EXISTS idx_agent_configurations_user_id ON agent_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_configurations_retell_agent_id ON agent_configurations(retell_agent_id);

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

    -- Raw Analysis Data from Retell AI
    analysis_data JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2),
    processing_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure one result per call
    UNIQUE(call_id)
);

-- Index for results lookup
CREATE INDEX IF NOT EXISTS idx_call_results_call_id ON call_results(call_id);
CREATE INDEX IF NOT EXISTS idx_call_results_scenario_type ON call_results(scenario_type);
CREATE INDEX IF NOT EXISTS idx_call_results_is_emergency ON call_results(is_emergency);

-- ============================================
-- 6. TRIGGERS FOR UPDATED_AT
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
CREATE TRIGGER update_agent_configurations_updated_at
    BEFORE UPDATE ON agent_configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_transcripts_updated_at
    BEFORE UPDATE ON call_transcripts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_call_results_updated_at
    BEFORE UPDATE ON call_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE agent_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;

-- Agent Configurations Policies
CREATE POLICY "Users can view their own agent configurations"
    ON agent_configurations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own agent configurations"
    ON agent_configurations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own agent configurations"
    ON agent_configurations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own agent configurations"
    ON agent_configurations FOR DELETE
    USING (auth.uid() = user_id);

-- Calls Policies
CREATE POLICY "Users can view their own calls"
    ON calls FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own calls"
    ON calls FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own calls"
    ON calls FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own calls"
    ON calls FOR DELETE
    USING (auth.uid() = user_id);

-- Call Transcripts Policies
CREATE POLICY "Users can view transcripts of their own calls"
    ON call_transcripts FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

CREATE POLICY "Users can create transcripts for their own calls"
    ON call_transcripts FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

CREATE POLICY "Users can update transcripts of their own calls"
    ON call_transcripts FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

CREATE POLICY "Users can delete transcripts of their own calls"
    ON call_transcripts FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_transcripts.call_id
        AND calls.user_id = auth.uid()
    ));

-- Call Results Policies
CREATE POLICY "Users can view results of their own calls"
    ON call_results FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

CREATE POLICY "Users can create results for their own calls"
    ON call_results FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

CREATE POLICY "Users can update results of their own calls"
    ON call_results FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

CREATE POLICY "Users can delete results of their own calls"
    ON call_results FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM calls
        WHERE calls.id = call_results.call_id
        AND calls.user_id = auth.uid()
    ));

-- ============================================
-- 8. SERVICE ROLE BYPASS (For Webhooks)
-- ============================================
-- Note: Webhooks use the service_role key which bypasses RLS
-- No additional policies needed for webhook access

-- ============================================
-- SCHEMA COMPLETE
-- ============================================
-- Tables: agent_configurations, calls, call_transcripts, call_results
-- Triggers: Auto-update updated_at on all tables
-- RLS: User-scoped access control enabled
-- Indexes: Optimized for common queries
-- ============================================
