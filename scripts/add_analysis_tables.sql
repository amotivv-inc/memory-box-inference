-- SQL script to add analysis tables for the general analysis API
-- Run this script to add the necessary tables for conversation analysis functionality

-- Analysis configurations table
CREATE TABLE IF NOT EXISTS analysis_configs (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique names per organization
    UNIQUE(organization_id, name)
);

-- Index for efficient listing
CREATE INDEX IF NOT EXISTS idx_analysis_config_org ON analysis_configs(organization_id, is_active);

-- Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    analysis_config_id UUID REFERENCES analysis_configs(id) ON DELETE SET NULL,
    config_snapshot JSONB NOT NULL,  -- Config used at time of analysis
    analysis_type VARCHAR(100),      -- From config (intent, sentiment, etc.)
    results JSONB NOT NULL,          -- Flexible results structure
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Cache key: same request + same config = same result
    UNIQUE(request_id, analysis_config_id)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_analysis_request ON analysis_results(request_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_results(created_at);

-- Add comments for documentation
COMMENT ON TABLE analysis_configs IS 'Stores reusable analysis configurations for conversation analysis (intents, sentiments, topics, etc.)';
COMMENT ON TABLE analysis_results IS 'Stores the results of analysis performed on requests/responses';

COMMENT ON COLUMN analysis_configs.config IS 'JSON configuration defining the analysis type, categories, model settings, etc.';
COMMENT ON COLUMN analysis_results.config_snapshot IS 'The exact configuration used at the time of analysis (for reproducibility)';
COMMENT ON COLUMN analysis_results.results IS 'Flexible JSON structure containing the analysis results';
