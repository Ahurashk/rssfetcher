import asyncio, aiohttp, csv, time, os
import feedparser
from dateutil import parser as dtparser
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_feeds():
    with open("feeds.csv") as f:
        reader = csv.DictReader(f)
        return [(row["name"], row["url"], int(row["interval_sec"])) for row in reader]

def parse_feed(xml, feed_name):
    parsed = feedparser.parse(xml)
    entries = []
    for e in parsed.entries:
        try:
            ts_raw = e.get("published") or e.get("updated") or ""
            ts = dtparser.parse(ts_raw).astimezone().isoformat() if ts_raw else None
            entries.append({
                "title": e.get("title", ""),
                "content": e.get("summary", "") or e.get("description", ""),
                "published_utc": ts,
                "link": e.get("link", ""),
                "raw_xml": str(e),
                # no source_name – it's not in the schema
            })
        except Exception as ex:
            print(f"[WARN] Failed to parse entry: {ex}")
    return entries

async def fetch_and_store(session, feed_name, feed_url):
    try:
        async with session.get(feed_url, timeout=10) as r:
            xml = await r.text()
        items = parse_feed(xml, feed_name)
        for item in items:
            existing = supabase.table("items").select("id").eq("link", item["link"]).execute()
            if not existing.data:
                feed = supabase.table("feeds").select("id").eq("name", feed_name).execute()
                if feed.data:
                    item["feed_id"] = feed.data[0]["id"]
                else:
                    new_feed = supabase.table("feeds").insert({"name": feed_name, "url": feed_url}).execute()
                    item["feed_id"] = new_feed.data[0]["id"]
                supabase.table("items").insert(item).execute()
                print(f"[{feed_name}] Inserted: {item['title'][:60]}")
    except Exception as e:
        print(f"[ERROR] {feed_name}: {e}")

async def main():
    feeds = load_feeds()
    last_run = {f[1]: 0 for f in feeds}

    async with aiohttp.ClientSession() as session:
        while True:
            now = time.time()
            tasks = []
            for name, url, interval in feeds:
                if now - last_run[url] >= interval:
                    tasks.append(fetch_and_store(session, name, url))
                    last_run[url] = now
            if tasks:
                await asyncio.gather(*tasks)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
