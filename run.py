import os
import json
import time
import urllib.parse
from dotenv import load_dotenv
from src.notion_transmitter import transmit_to_notion
from src.state import is_processed, mark_processed

load_dotenv()

from src.discovery import fetch_discovered_urls, deduplicate_with_llm
from src.state import is_processed
from src.ingestion import extract_clean_text
from src.analyzer import analyze_article

def generate_youtube_search_url(query_topic: str) -> str:
    """Constructs a direct link to YouTube search results for the topic."""
    search_term = f"{query_topic} UPSC current affairs analysis"
    encoded_query = urllib.parse.quote_plus(search_term)
    return f"https://www.youtube.com/results?search_query={encoded_query}"

def run_presentation_test():
    print("=== STARTING LOCAL PRESENTATION TEST (LAYER 0 to 3.5) ===")
    
    raw_candidates = fetch_discovered_urls(limit_per_feed=3)
    if not raw_candidates:
        return
        
    clustered_candidates = deduplicate_with_llm(raw_candidates)

    for article in clustered_candidates:
        url = article["url"]
        
        if is_processed(url):
            print(f"⏭️ [State] Skipping: {article['title']}")
            continue
            
        print(f"\n🔥 [Pipeline] Processing: {article['title']}")
        
        extracted_data = extract_clean_text(url)
        
        if extracted_data and extracted_data.get("text"):
            # Layer 3: Pydantic-enforced analysis via Gemini 2.5 Pro
            upsc_payload = analyze_article(extracted_data["text"], url)
            
            if upsc_payload:
                # Layer 3.5: Instant Python URL bridge
                youtube_url = generate_youtube_search_url(upsc_payload['headline'])
                
                final_payload = {
                    "source_url": url,
                    "youtube_search": youtube_url,
                    "analysis": upsc_payload
                }
                transmit_to_notion(upsc_payload, url, youtube_url)
                mark_processed(article['url'])
                    # TRANSMIT!
                    
                
                # Sleep to respect rate limits
                time.sleep(15)

if __name__ == "__main__":
    run_presentation_test()