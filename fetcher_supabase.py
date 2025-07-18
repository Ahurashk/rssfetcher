import asyncio, aiohttp, csv, time, os
from datetime import datetime
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

async def fetch_and_store(session, feed_name, feed_url):
    try:
        async with session.get(feed_url, timeout=10) as r:
            xml = await r.text()
        feed = supabase.table("feeds").select("id").eq("name", feed_name).execute()
        if feed.data:
            feed_id = feed.data[0]["id"]
        else:
            new_feed = supabase.table("feeds").insert({"name": feed_name, "url": feed_url}).execute()
            feed_id = new_feed.data[0]["id"]
        supabase.table("raw_feeds").insert({
            "feed_id": feed_id,
            "fetched_at": datetime.utcnow().isoformat(),
            "raw_xml": xml,
        }).execute()
        print(f"[{feed_name}] Raw XML saved at {datetime.utcnow().isoformat()}")
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
                    async def wrap(name=name, url=url):
                        try:
                            await fetch_and_store(session, name, url)
                        except Exception as ex:
                            print(f"[CRITICAL] {name}: {ex}")
                        finally:
                            last_run[url] = int(time.time())
                    tasks.append(wrap())
            if tasks:
                await asyncio.gather(*tasks)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
