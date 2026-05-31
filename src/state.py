import os
import json
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

HISTORY_FILE = "history.json"

def sanitize_url(url: str) -> str:
    """
    Cleans the URL by converting to lowercase, removing tracking parameters (?), 
    stripping anchor fragments (#), and removing trailing slashes.
    """
    parsed = urlparse(url)
    
    # Reconstruct URL keeping only scheme, netloc, and path. 
    # Force netloc and path to lowercase for exact matching.
    clean_url = urlunparse((
        parsed.scheme.lower(), 
        parsed.netloc.lower(), 
        parsed.path.lower(), 
        '', '', ''
    ))
    
    return clean_url.rstrip('/')

def _load_state() -> dict:
    """Helper function to safely load the JSON database."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ [Layer 2] {HISTORY_FILE} corrupted. Initializing fresh state.")
        return {}

def is_processed(url: str) -> bool:
    """Checks if the sanitized URL exists in the JSON database."""
    state = _load_state()
    target = sanitize_url(url)
    return target in state

def mark_processed(original_url: str) -> None:
    """
    Records the URL into the JSON database with a UTC timestamp,
    using an atomic write to guarantee file integrity.
    """
    state = _load_state()
    target_key = sanitize_url(original_url)
    
    # Create the structured audit record
    state[target_key] = {
        "original_url": original_url,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS"
    }
    
    # Atomic Write: Write to temp file, then rename
    temp_file = f"{HISTORY_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        
    os.replace(temp_file, HISTORY_FILE)
    print(f"💾 [Layer 2] Safely locked URL into {HISTORY_FILE}.")