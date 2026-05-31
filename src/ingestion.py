import requests
from newspaper import Article

# Standard desktop browser headers to bypass basic anti-scraping walls
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def fetch_raw_html(url: str) -> str:
    """Fetches raw HTML directly using customized headers to handle tricky news DOMs."""
    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ [Layer 1] Network error fetching {url}: {e}")
        return ""

# def extract_clean_text(url: str) -> dict:
    """
    Downloads an article URL, strips away HTML scaffolding, tracking nodes, 
    and sidebars, then returns a normalized data package.
    """
    print(f"📥 [Layer 1] Initializing extraction for: {url}")
    
    # Initialize the newspaper Article instance
    article = Article(url)
    
    try:
        # Step 1: Use custom fetched HTML to bypass aggressive anti-bot proxies
        raw_html = fetch_raw_html(url)
        if not raw_html:
            return {}
            
        # Step 2: Pass raw HTML directly into newspaper4k for parsing
        article.set_html(raw_html)
        article.parse()
        
        # Step 3: Validate the extraction output
        if not article.text or len(article.text.strip()) < 100:
            print(f"⚠️ [Layer 1] Warning: Extracted text is suspiciously short or empty.")
            return {}
            
        # Step 4: Map to the standardized output structure
        payload = {
            "title": article.title.strip(),
            "text": article.text.strip(),
            "source_url": url,
            "author": ", ".join(article.authors) if article.authors else "Unknown"
        }
        
        print(f"✅ [Layer 1] Successfully extracted '{payload['title']}' ({len(payload['text'])} characters)")
        return payload

    except Exception as e:
        print(f"❌ [Layer 1] Critical extraction failure on {url}: {e}")
        return {}
    
def extract_clean_text(url: str) -> dict:
    print(f"📥 [Layer 1] Initializing extraction for: {url}")
    
    try:
        raw_html = fetch_raw_html(url)
        if not raw_html:
            return {}
            
        # FIX: Pass the raw HTML directly into the Article constructor or set the property
        article = Article(url, fetch_images=False)
        article.html = raw_html # Inject the HTML we already downloaded
        article.parse()
        
        if not article.text or len(article.text.strip()) < 100:
            print(f"⚠️ [Layer 1] Warning: Extracted text is suspiciously short or empty.")
            return {}
            
        payload = {
            "title": article.title.strip() if article.title else "Untitled",
            "text": article.text.strip(),
            "source_url": url,
            "author": ", ".join(article.authors) if article.authors else "Unknown"
        }
        
        print(f"✅ [Layer 1] Successfully extracted '{payload['title']}' ({len(payload['text'])} characters)")
        return payload

    except Exception as e:
        print(f"❌ [Layer 1] Critical extraction failure on {url}: {e}")
        return {}