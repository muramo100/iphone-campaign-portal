#!/usr/bin/env python3
import feedparser, json, re, hashlib, time
from datetime import datetime, timezone
from urllib.parse import urlparse

KEYWORDS = [
    r"\biPhone\b", r"アイフォン", r"アイホン",
    r"iPhone\s?(1[0-9]|SE|XR|XS|X|8|7)",
    r"16\s?e", r"15\s?Pro", r"15\s?Plus", r"14\s?Pro", r"SE\s?3"
]
NEGATIVE = [r"\bRumor\b", r"噂", r"リーク"]

def looks_relevant(title, summary):
    text = f"{title} {summary}".lower()
    if any(re.search(pat, text, re.I) for pat in KEYWORDS):
        if any(re.search(pat, text, re.I) for pat in NEGATIVE):
            return False
        return True
    return False

def norm_source(url):
    return urlparse(url).netloc.replace("www.","")

def main():
    with open("scrape/feeds.txt","r",encoding="utf-8") as f:
        feeds=[l.strip() for l in f if l.strip() and not l.startswith("#")]

    items=[]
    now_iso=datetime.now(timezone.utc).isoformat()

    for feed in feeds:
        d=feedparser.parse(feed)
        for e in d.entries:
            title=e.get("title",""); summary=e.get("summary",""); link=e.get("link","")
            if not link or not title: continue
            if not looks_relevant(title, summary): continue

            t=e.get("published_parsed") or e.get("updated_parsed")
            ts=int(time.mktime(t)) if t else int(time.time())
            iso=datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            badges=["新着"] if (time.time()-ts)<=24*3600 else []

            uid=hashlib.md5(link.encode("utf-8")).hexdigest()[:12]
            items.append({
                "id":uid, "title":title,
                "summary":re.sub(r"<[^>]+>","",summary)[:240],
                "url":link, "source":norm_source(link),
                "published_at":iso, "badges":badges
            })

    uniq={it["id"]:it for it in items}
    items=sorted(uniq.values(), key=lambda x:x["published_at"], reverse=True)
    out={"generated_at":now_iso, "count":len(items), "items":items[:300]}

    with open("public/data/campaigns.json","w",encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__=="__main__":
    main()
