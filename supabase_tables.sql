-- OpenRouter Scraper Database Tables
-- Run these SQL statements in your Supabase SQL Editor

-- Table for OpenRouter Models data
CREATE TABLE openrouter_models (
  id SERIAL PRIMARY KEY,
  rank INTEGER NOT NULL,
  model_name TEXT NOT NULL,
  author TEXT NOT NULL,
  tokens TEXT,
  trend_percentage TEXT,
  trend_direction TEXT,
  trend_icon TEXT,
  trend_color TEXT,
  model_url TEXT,
  author_url TEXT,
  time_period TEXT NOT NULL,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for OpenRouter Apps data
CREATE TABLE openrouter_apps (
  id SERIAL PRIMARY KEY,
  rank INTEGER NOT NULL,
  app_name TEXT NOT NULL,
  description TEXT,
  tokens TEXT,
  is_new BOOLEAN DEFAULT FALSE,
  app_url TEXT,
  domain TEXT,
  image_url TEXT,
  time_period TEXT NOT NULL,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_openrouter_models_time_period ON openrouter_models(time_period);
CREATE INDEX idx_openrouter_models_scraped_at ON openrouter_models(scraped_at);
CREATE INDEX idx_openrouter_models_rank ON openrouter_models(rank);

CREATE INDEX idx_openrouter_apps_time_period ON openrouter_apps(time_period);
CREATE INDEX idx_openrouter_apps_scraped_at ON openrouter_apps(scraped_at);
CREATE INDEX idx_openrouter_apps_rank ON openrouter_apps(rank);

-- Optional: Create a view for latest models by time period
CREATE VIEW latest_models AS
SELECT DISTINCT ON (time_period, rank) *
FROM openrouter_models
ORDER BY time_period, rank, scraped_at DESC;

-- Optional: Create a view for latest apps by time period  
CREATE VIEW latest_apps AS
SELECT DISTINCT ON (time_period, rank) *
FROM openrouter_apps
ORDER BY time_period, rank, scraped_at DESC;
