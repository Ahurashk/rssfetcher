# 📰 RSS Fetcher to Supabase

A cloud-based Python worker that fetches real-time financial news from RSS feeds and pushes them into Supabase for downstream use with agents, LLMs, dashboards, or backtesting pipelines.

---

## ✅ What It Does

- Pulls data from multiple RSS feeds at custom intervals
- Normalizes headlines and stores them into `feeds` and `items` tables in Supabase
- Automatically deduplicates using link + feed
- Can be deployed locally or on Render.com (as a background worker)

---

## 📂 File Structure

```
fetcher_supabase/
├── fetcher_supabase.py       # Main fetcher script
├── feeds.csv                 # Feed source list + polling intervals
├── requirements.txt          # Python dependencies
└── .gitignore                # Ignores .env, venv, and cache
```

---

## ⚙️ feeds.csv Format

```csv
name,url,interval_sec
FinancialJuice,https://www.financialjuice.com/feed.ashx?xy=rss,30
WSJ - Market News,https://feeds.content.dowjones.io/public/rss/RSSMarketsMain,90
...
```

Each row controls how often each feed is polled independently.

---

## 🚀 Deploy on Render.com

1. Push this folder to a GitHub repo
2. Go to [https://dashboard.render.com](https://dashboard.render.com)
3. Click **New → Background Worker**
4. Fill in:

- **Start Command:** `python fetcher_supabase.py`
- **Environment Variables:**
    - `SUPABASE_URL`: your Supabase project URL
    - `SUPABASE_KEY`: anon or service role key

---

## 🔒 .env Format (local use)

```
SUPABASE_URL="https://yourproject.supabase.co"
SUPABASE_KEY="your-secret-api-key"
```

---

## 📊 Supabase Schema

Run this in Supabase SQL editor:

```sql
CREATE TABLE feeds (
  id SERIAL PRIMARY KEY,
  name TEXT,
  url TEXT UNIQUE,
  interval_sec INTEGER DEFAULT 30
);

CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  feed_id INTEGER REFERENCES feeds(id),
  title TEXT,
  content TEXT,
  published_utc TIMESTAMP,
  link TEXT,
  raw_xml TEXT,
  UNIQUE(feed_id, link)
);
```

---

## 🧠 Next Steps

- Add LLM-based classifiers to tag headlines
- Query recent headlines via OpenAI/Claude
- Visualize or summarize daily market movers
- Plug into agent-based macro analysis

