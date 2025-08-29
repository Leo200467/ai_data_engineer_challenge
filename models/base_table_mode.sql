CREATE TABLE IF NOT EXISTS raw_ads_spend (
    date TEXT,
    platform TEXT,
    account TEXT,
    campaign TEXT,
    country TEXT,
    device TEXT,
    spend REAL,
    clicks INTEGER,
    impressions INTEGER,
    conversions INTEGER,
    load_date TEXT,
    source_file_name TEXT
);