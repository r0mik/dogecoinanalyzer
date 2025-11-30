-- Initialize database schema for DogeAnalyze
-- This script runs automatically when PostgreSQL container starts for the first time

-- Market Data Table
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    price_usd DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    price_change_24h DECIMAL(10, 4),
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_created_at ON market_data(created_at);

-- Analysis Results Table
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1h', '4h', '24h'
    predicted_price DECIMAL(20, 8),
    confidence_score INTEGER,  -- 0-100
    trend_direction VARCHAR(20),  -- 'bullish', 'bearish', 'neutral'
    technical_indicators TEXT,  -- JSON string
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analysis_timestamp ON analysis_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_analysis_timeframe ON analysis_results(timeframe);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at);

-- Script Status Table
CREATE TABLE IF NOT EXISTS script_status (
    id SERIAL PRIMARY KEY,
    script_name VARCHAR(50) NOT NULL UNIQUE,  -- 'collector', 'analyzer'
    last_run TIMESTAMP,
    status VARCHAR(20),  -- 'running', 'success', 'error'
    message TEXT,
    next_run TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_script_name ON script_status(script_name);

-- Insert initial script status records
INSERT INTO script_status (script_name, status) 
VALUES ('collector', 'pending'), ('analyzer', 'pending')
ON CONFLICT (script_name) DO NOTHING;

