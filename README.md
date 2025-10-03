# OpenRouter Scraper

Automated scraper for OpenRouter data that runs on GitHub Actions and stores results in Supabase.

## Setup

### 1. Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Create two tables in your Supabase database:

**Table: `openrouter_models`**
```sql
CREATE TABLE openrouter_models (
  id SERIAL PRIMARY KEY,
  rank INTEGER,
  model_name TEXT,
  author TEXT,
  tokens TEXT,
  trend_percentage TEXT,
  trend_direction TEXT,
  trend_icon TEXT,
  trend_color TEXT,
  model_url TEXT,
  author_url TEXT,
  time_period TEXT,
  scraped_at TIMESTAMP WITH TIME ZONE
);
```

**Table: `openrouter_apps`**
```sql
CREATE TABLE openrouter_apps (
  id SERIAL PRIMARY KEY,
  rank INTEGER,
  app_name TEXT,
  description TEXT,
  tokens TEXT,
  is_new BOOLEAN,
  app_url TEXT,
  domain TEXT,
  image_url TEXT,
  time_period TEXT,
  scraped_at TIMESTAMP WITH TIME ZONE
);
```

### 2. GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key

### 3. GitHub Actions

The workflow is configured to run every 6 hours automatically. You can also trigger it manually from the Actions tab.

## Files

- `scrapers/scraper_models.py` - Scrapes OpenRouter model rankings
- `scrapers/scraper_apps.py` - Scrapes OpenRouter app rankings  
- `requirements.txt` - Python dependencies
- `.github/workflows/scrape.yml` - GitHub Actions workflow

## Usage

The scrapers will automatically run on GitHub Actions and save data to your Supabase database. No manual intervention required.

## Data Structure

### Models Data
- rank, model_name, author, tokens, trend_percentage, trend_direction, trend_icon, trend_color, model_url, author_url, time_period, scraped_at

### Apps Data  
- rank, app_name, description, tokens, is_new, app_url, domain, image_url, time_period, scraped_at
