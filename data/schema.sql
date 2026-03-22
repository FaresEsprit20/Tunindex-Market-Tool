-- data/schema.sql

CREATE TABLE IF NOT EXISTS stocks (
    symbol TEXT PRIMARY KEY,
    company_name TEXT,

    -- Classification
    ownership_type TEXT,
    activity_type TEXT,

    -- Market Data
    price NUMERIC,
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    volume NUMERIC,
    market_cap NUMERIC,

    -- Fundamentals
    eps NUMERIC,
    book_value_per_share NUMERIC,
    total_equity NUMERIC,
    shares_outstanding NUMERIC,

    pe_ratio NUMERIC,
    roe NUMERIC,
    roa NUMERIC,
    debt_equity NUMERIC,
    profit_margin NUMERIC,

    -- Valuation
    fair_value NUMERIC,
    margin_of_safety NUMERIC,

    -- Metadata
    source TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional indexes (recommended for performance)
CREATE INDEX IF NOT EXISTS idx_stocks_mos ON stocks(margin_of_safety);
CREATE INDEX IF NOT EXISTS idx_stocks_price ON stocks(price);
CREATE INDEX IF NOT EXISTS idx_stocks_source ON stocks(source);