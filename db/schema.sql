-- BDC Portfolio Analysis Database Schema
-- Version 1.0
-- Supports: Portfolio overlap analysis, industry concentration, time series tracking
-- Future-ready: Columns for semantic search/embeddings (populated later)

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Business Development Companies
CREATE TABLE IF NOT EXISTS bdc (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cik TEXT UNIQUE,
    total_assets REAL,
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio Companies (the borrowers/investees)
CREATE TABLE IF NOT EXISTS portfolio_company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Core identification
    normalized_name TEXT NOT NULL,
    
    -- Original free text - preserved for future semantic search
    business_desc TEXT,
    
    -- Structured classification (populated where available)
    sic_code TEXT,
    naics_code TEXT,
    
    -- Our standardized classification
    assigned_industry TEXT,
    classification_method TEXT CHECK(classification_method IN ('SIC', 'NAICS', 'KEYWORD', 'LLM', 'MANUAL', NULL)),
    confidence_score REAL CHECK(confidence_score >= 0 AND confidence_score <= 1),
    
    -- Standard identifiers (for future entity resolution)
    lei TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(normalized_name)
);

-- Industry Classification Reference Table
CREATE TABLE IF NOT EXISTS industry (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sector TEXT,           -- Higher-level grouping
    parent_sector TEXT,    -- Even higher level if needed
    description TEXT
);

-- ============================================================================
-- INVESTMENT POSITIONS (the core analytical table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS investment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign keys
    bdc_ticker TEXT NOT NULL REFERENCES bdc(ticker),
    company_id INTEGER NOT NULL REFERENCES portfolio_company(id),
    
    -- Investment details
    investment_type TEXT,           -- 'First lien senior secured loan', 'Preferred units', etc.
    asset_class TEXT,               -- 'Debt' or 'Equity' (derived)
    
    -- Amounts
    fair_value REAL,
    cost REAL,
    principal REAL,                 -- Debt only
    shares REAL,                    -- Equity only
    
    -- Rate information (debt only)
    interest_rate REAL,
    spread REAL,
    rate_type TEXT,                 -- 'SOFR', 'Prime', 'Fixed'
    
    -- Dates
    maturity_date DATE,
    acquisition_date DATE,
    
    -- Time series dimensions (CRITICAL for tracking changes)
    period_end DATE NOT NULL,       -- e.g., 2024-09-30
    filing_date DATE,               -- When the 10-K/10-Q was filed
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,         -- NULL for annual (10-K)
    
    -- Source tracking
    source_filing TEXT,             -- e.g., '10-K', '10-Q'
    investment_id_raw TEXT,         -- Original XBRL ID if available
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate positions for same period
    UNIQUE(bdc_ticker, company_id, investment_type, period_end, principal, fair_value)
);

-- ============================================================================
-- FUTURE EXTENSION: Embeddings for Semantic Search
-- ============================================================================

-- This table will be populated later when/if we add semantic search
-- Keeping it separate allows Phase 1 to work without vector dependencies
CREATE TABLE IF NOT EXISTS company_embedding (
    company_id INTEGER PRIMARY KEY REFERENCES portfolio_company(id),
    embedding BLOB,                 -- Serialized numpy array or similar
    model_name TEXT,                -- e.g., 'text-embedding-3-small'
    model_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR COMMON QUERIES
-- ============================================================================

-- Portfolio overlap queries
CREATE INDEX IF NOT EXISTS idx_investment_company ON investment(company_id);
CREATE INDEX IF NOT EXISTS idx_investment_bdc ON investment(bdc_ticker);
CREATE INDEX IF NOT EXISTS idx_investment_period ON investment(period_end);

-- Industry concentration queries
CREATE INDEX IF NOT EXISTS idx_company_industry ON portfolio_company(assigned_industry);

-- Time series queries
CREATE INDEX IF NOT EXISTS idx_investment_time ON investment(bdc_ticker, period_end);
CREATE INDEX IF NOT EXISTS idx_investment_fiscal ON investment(fiscal_year, fiscal_quarter);

-- Full text search on business descriptions (SQLite FTS5)
-- Uncomment if FTS5 is available:
-- CREATE VIRTUAL TABLE IF NOT EXISTS company_fts USING fts5(
--     normalized_name,
--     business_desc,
--     content='portfolio_company',
--     content_rowid='id'
-- );

-- ============================================================================
-- VIEWS FOR COMMON ANALYSIS PATTERNS
-- ============================================================================

-- Portfolio overlap: companies held by multiple BDCs
CREATE VIEW IF NOT EXISTS v_overlap_companies AS
SELECT 
    pc.id as company_id,
    pc.normalized_name,
    pc.assigned_industry,
    COUNT(DISTINCT i.bdc_ticker) as bdc_count,
    GROUP_CONCAT(DISTINCT i.bdc_ticker) as bdcs_holding,
    SUM(i.fair_value) as total_fair_value,
    MAX(i.period_end) as latest_period
FROM portfolio_company pc
JOIN investment i ON pc.id = i.company_id
GROUP BY pc.id, pc.normalized_name, pc.assigned_industry
HAVING COUNT(DISTINCT i.bdc_ticker) > 1;

-- Industry concentration across all BDCs
CREATE VIEW IF NOT EXISTS v_industry_concentration AS
SELECT 
    pc.assigned_industry,
    i.bdc_ticker,
    i.period_end,
    COUNT(DISTINCT pc.id) as company_count,
    SUM(i.fair_value) as total_fair_value,
    SUM(i.fair_value) * 100.0 / SUM(SUM(i.fair_value)) OVER (PARTITION BY i.bdc_ticker, i.period_end) as pct_of_portfolio
FROM investment i
JOIN portfolio_company pc ON i.company_id = pc.id
WHERE pc.assigned_industry IS NOT NULL
GROUP BY pc.assigned_industry, i.bdc_ticker, i.period_end;

-- BDC summary statistics
CREATE VIEW IF NOT EXISTS v_bdc_summary AS
SELECT 
    i.bdc_ticker,
    b.name as bdc_name,
    i.period_end,
    COUNT(DISTINCT i.company_id) as company_count,
    COUNT(*) as position_count,
    SUM(i.fair_value) as total_fair_value,
    SUM(CASE WHEN i.asset_class = 'Debt' THEN i.fair_value ELSE 0 END) as debt_fair_value,
    SUM(CASE WHEN i.asset_class = 'Equity' THEN i.fair_value ELSE 0 END) as equity_fair_value
FROM investment i
JOIN bdc b ON i.bdc_ticker = b.ticker
GROUP BY i.bdc_ticker, b.name, i.period_end;

-- ============================================================================
-- SEED DATA: Standard Industry Classifications
-- ============================================================================

INSERT OR IGNORE INTO industry (code, name, sector) VALUES
    ('SOFTWARE', 'Software/Technology', 'Technology'),
    ('HEALTHCARE', 'Healthcare', 'Healthcare'),
    ('HEALTHCARE_SERVICES', 'Healthcare Services', 'Healthcare'),
    ('BUSINESS_SERVICES', 'Business Services', 'Services'),
    ('FINANCIAL_SERVICES', 'Financial Services', 'Financial'),
    ('CONSUMER', 'Consumer Products', 'Consumer'),
    ('CONSUMER_SERVICES', 'Consumer Services', 'Consumer'),
    ('INDUSTRIAL', 'Industrial/Manufacturing', 'Industrial'),
    ('TRANSPORTATION', 'Transportation & Logistics', 'Industrial'),
    ('ENERGY', 'Energy', 'Energy'),
    ('MEDIA', 'Media & Entertainment', 'Media'),
    ('TELECOM', 'Telecommunications', 'Technology'),
    ('REAL_ESTATE', 'Real Estate', 'Real Estate'),
    ('EDUCATION', 'Education', 'Services'),
    ('GOVERNMENT', 'Government Services', 'Services'),
    ('OTHER', 'Other', 'Other');
