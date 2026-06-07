import os
import json
import feedparser
import requests
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

import datetime
from dateutil import parser

# High-yield UPSC feeds
UPSC_FEEDS = {
    "PIB - National (English)": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1&reg=1",
    "The Hindu - National": "https://www.thehindu.com/news/national/feeder/default.rss",
    "The Hindu - Editorial": "https://www.thehindu.com/opinion/feeder/default.rss"
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# --- LAYER 0.5: PYDANTIC SCHEMAS ---
class ClusteredEvent(BaseModel):
    theme: str = Field(description="The core UPSC news event or topic (e.g., 'RBI Repo Rate Hike').")
    primary_url: str = Field(description="The single best, most authoritative URL to use for this event.")
    duplicate_urls_dropped: list[str] = Field(description="URLs of duplicate articles covering the same event that are being skipped.")

class DeduplicatedBatch(BaseModel):
    events: list[ClusteredEvent]

# --- LAYER 0: RAW DISCOVERY ---
def fetch_discovered_urls(limit_per_feed: int = 5) -> list[dict]:
    """Scans all target RSS feeds and returns a list of newly discovered articles."""
    discovered_articles = []
    print(f"📡 [Layer 0] Initializing RSS discovery across {len(UPSC_FEEDS)} streams...")
    
    for feed_name, feed_url in UPSC_FEEDS.items():
        try:
            response = requests.get(feed_url, headers=BROWSER_HEADERS, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            
            entries = feed.entries[:limit_per_feed]
            for entry in entries:
                url = getattr(entry, 'link', '').strip()
                title = getattr(entry, 'title', 'Untitled').strip()
                
                # --- NEW: Exact Publish Date Extraction ---
                raw_date = entry.get('published') or entry.get('updated')
                if raw_date:
                    try:
                        parsed_date = parser.parse(raw_date).strftime('%Y-%m-%d')
                    except Exception:
                        # Fallback if the site uses a weird custom date string
                        parsed_date = datetime.datetime.now().strftime('%Y-%m-%d')
                else:
                    # Fallback to today if the site hides the date entirely
                    parsed_date = datetime.datetime.now().strftime('%Y-%m-%d')
                # ------------------------------------------
                
                if url:
                    discovered_articles.append({
                        "title": title, 
                        "url": url, 
                        "source": feed_name,
                        "publish_date": parsed_date  # <--- Date is now locked in
                    })
                    
        except Exception as e:
            print(f"❌ [Layer 0] Failed to fetch '{feed_name}': {e}")
            
    print(f"📊 [Layer 0] Raw discovery complete. Candidate articles: {len(discovered_articles)}")
    return discovered_articles

# --- LAYER 0.5: SEMANTIC CLUSTERING ---
def deduplicate_with_llm(raw_articles: list[dict]) -> list[dict]:
    """Uses Gemini 2.5 Flash to group identical news stories and pick one primary link."""
    # Defensive Check 1: Empty input handles safely
    if not raw_articles:
        print("⚠️ [Layer 0.5] No raw articles provided to cluster. Returning empty list.")
        return []

    print(f"🧠 [Layer 0.5] Passing {len(raw_articles)} headlines to Gemini 2.5 Flash for semantic clustering...")
    
    catalog = "\n".join([f"- Title: {a['title']} | URL: {a['url']} | Source: {a['source']}" for a in raw_articles])
    
    sys_instruct = (
        "You are a UPSC Chief Editor. Review the following daily news catalog. "
        "Group articles covering the exact same event. For each event, select the SINGLE most comprehensive source URL. "
        "Favor Explained/Editorial sections over standard news if duplicates exist."
    )
    
    try:
        client = genai.Client()
        
        # Explicit configuration objects prevent parsing bugs across SDK versions
        config = types.GenerateContentConfig(
            system_instruction=sys_instruct,
            response_mime_type="application/json",
            response_schema=DeduplicatedBatch,
            temperature=0.1
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=catalog,
            config=config
        )
        
        batch_data = json.loads(response.text)
        final_urls = []
        
        for event in batch_data.get('events', []):
            primary = event.get('primary_url')
            if primary:
                # Clear trailing slash variances to match correctly
                primary_lookup = primary.strip().rstrip('/')
                
                # Find matching original entry to retain title and source tracking
                original_dict = next(
                    (item for item in raw_articles if item["url"].strip().rstrip('/') == primary_lookup), 
                    None
                )
                
                if original_dict:
                    final_urls.append(original_dict)
                else:
                    # Fallback: if the LLM hallucinated a clean URL formatting, preserve the string anyway
                    final_urls.append({"title": event.get('theme'), "url": primary, "source": "LLM Cluster"})
                    
        print(f"✂️ [Layer 0.5] Clustering complete. Reduced {len(raw_articles)} links down to {len(final_urls)} unique events.")
        return final_urls

    except Exception as e:
        # Defensive Check 2: Absolute safety fallback to prevent upstream crashes
        print(f"❌ [Layer 0.5] Semantic clustering failed: {e}. Falling back to raw list.")
        return raw_articles