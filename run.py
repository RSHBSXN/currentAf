import os
import time
import urllib.parse
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from src.discovery import fetch_discovered_urls, deduplicate_with_llm
from src.state import is_processed, mark_processed
from src.ingestion import extract_clean_text
from src.analyzer import analyze_article
from src.notion_transmitter import transmit_to_notion

def generate_youtube_search_url(query_topic: str) -> str:
    """Constructs a direct link to YouTube search results for the topic."""
    search_term = f"{query_topic} UPSC current affairs analysis"
    encoded_query = urllib.parse.quote_plus(search_term)
    return f"https://www.youtube.com/results?search_query={encoded_query}"

def run_daily_sync():
    print("\n=== 🚀 STARTING DAILY UPSC AUTOMATION SYNC ===")
    
    # Scanning feeds for production volume
    raw_candidates = fetch_discovered_urls(limit_per_feed=10)
    if not raw_candidates:
        print("⚠️ No articles found in feeds today. Exiting.")
        return
        
    print(f"📊 Discovered {len(raw_candidates)} raw candidate URLs.")
    clustered_candidates = deduplicate_with_llm(raw_candidates)
    print(f"✂️ Reduced to {len(clustered_candidates)} unique events.")

    # Tracking for the final log summary
    success_count = 0
    error_count = 0
    skip_count = 0

    for article in clustered_candidates:
        url = article["url"]
        
        if is_processed(url):
            print(f"⏭️ [State] Skipping (Already Processed): {article['title']}")
            skip_count += 1
            continue
            
        print(f"\n🔥 [Pipeline] Processing: {article['title']}")
        
        try:
            # Layer 1: Extraction
            extracted_data = extract_clean_text(url)
            
            if extracted_data and extracted_data.get("text"):
                # Layer 2: Analysis via Gemini
                upsc_payload = analyze_article(extracted_data["text"], url)
                
                if upsc_payload:
                    # 👇 THE GATEKEEPER CHECK 👇
                    if not upsc_payload.get('is_upsc_relevant', True):
                        print(f"🗑️ [Gatekeeper] Dropping irrelevant article: {article['title']}")
                        mark_processed(url)  # Save to history so we don't re-process this junk tomorrow
                        skip_count += 1
                        continue             # Skip Notion completely and go to the next article
                    # 👆 ======================= 👆

                    # Safely get the headline now that we know it's a relevant article
                    headline_text = upsc_payload.get('headline') or 'Untitled UPSC Topic'
                    youtube_url = generate_youtube_search_url(headline_text)
                    
                    # --- ATTACH EXACT RSS PUBLISH DATE ---
                    # Bypasses LLM date estimation completely for 100% accuracy
                    upsc_payload['article_date'] = article.get('publish_date')
                    
                    # --- ATOMIC TRANSACTION BLOCK ---
                    try:
                        # 1. Attempt to transmit to Notion
                        transmit_to_notion(upsc_payload, url, youtube_url)
                        
                        # 2. ONLY if no errors, mark as processed
                        mark_processed(url)
                        print(f"✅ Success & Logged: {headline_text}")
                        success_count += 1
                        
                    except Exception as e:
                        print(f"❌ Transmission failed for {url}: {e}")
                        error_count += 1
                    # --------------------------------
                    
                    # Sleep to respect rate limits (Notion & LLM)
                    time.sleep(15)
                else:
                    print(f"⚠️ Analysis returned empty payload for {url}.")
                    error_count += 1
            else:
                print(f"⚠️ Failed to extract readable text for {url}.")
                error_count += 1
                
        except Exception as e:
            # Catches unexpected errors (like bad HTML parsing) so the loop doesn't break
            print(f"❌ Unexpected error processing {url}: {e}")
            error_count += 1

    # Final Execution Summary
    print("\n=== 🏁 DAILY SYNC COMPLETE ===")
    print(f"✅ Succeeded: {success_count} | ⏭️ Skipped: {skip_count} | ❌ Errors: {error_count}\n")

if __name__ == "__main__":
    try:
        run_daily_sync()
    except KeyboardInterrupt:
        print("\n🛑 Sync forcefully interrupted by user (Ctrl+C).")
    except Exception as e:
        print(f"\n💥 CRITICAL PIPELINE FAILURE: {e}")