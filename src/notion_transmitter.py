import os
from notion_client import Client

def transmit_to_notion(payload: dict, source_url: str, youtube_url: str):
    """
    Transmits the parsed analysis payload into the Notion database using the official SDK.
    """
    # Using your existing NOTION_API_KEY env variable name
    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_DATABASE_ID")

    # Helper: Create standard bullet points with safety truncation
    def bullet(text):
        return {
            "object": "block", 
            "type": "bulleted_list_item", 
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": str(text)[:2000]}}]
            }
        }

    # Helper: Create Toggles for Mains content (collapsible)
    def toggle(title, items):
        if not items:
            return None
        return {
            "object": "block", 
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": title}, "annotations": {"bold": True}}],
                "children": [bullet(item) for item in items if item]
            }
        }

    # --- Construct the Page Blocks (Body) ---
    blocks = []

    # 1. YouTube Concept Briefing Callout
    if youtube_url:
        blocks.append({
            "object": "block", "type": "callout", "callout": {
                "rich_text": [
                    {"type": "text", "text": {"content": "🎥 Concept Briefing: "}, "annotations": {"bold": True}}, 
                    {"type": "text", "text": {"content": "Find Lecture on YouTube", "link": {"url": youtube_url}}}
                ],
                "icon": {"type": "emoji", "emoji": "💡"}
            }
        })

    # 2. Syllabus Keywords Focus
    if payload.get('syllabus_topics'):
        topics_str = " | ".join(payload['syllabus_topics'])
        blocks.append({
            "object": "block", "type": "callout", "callout": {
                "rich_text": [{"type": "text", "text": {"content": f"Syllabus Focus: {topics_str}"}, "annotations": {"bold": True, "color": "blue"}}],
                "icon": {"type": "emoji", "emoji": "🏷️"}
            }
        })

    # 3. Core Context (Tutor Breakdown Paragraph)
    if payload.get('core_context'):
        blocks.append({
            "object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": payload['core_context'][:2000]}}]
            }
        })

    # 4. Prelims Pillars & Official Citations
    if payload.get('prelims_facts') or payload.get('official_citations'):
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🎯 Prelims Pillars"}}]}})
        
        # Inject official citations at the top of Prelims if they exist
        if payload.get('official_citations'):
            for citation in payload['official_citations']:
                blocks.append(bullet(f"🏛️ Citation: {citation}"))
                
        if payload.get('prelims_facts'):
            for fact in payload['prelims_facts']:
                blocks.append(bullet(fact))

    # 5. Mains Ammunition (Collapsible Headers)
    mains_blocks = []
    
    if payload.get('key_arguments'):
        mains_blocks.append(toggle("Key Arguments", payload['key_arguments']))
    if payload.get('way_forward'):
        mains_blocks.append(toggle("Way Forward", payload['way_forward']))
    if payload.get('mains_case_study'):
        mains_blocks.append(toggle("Case Study Application", [payload['mains_case_study']]))
        
    # Clean out any empty/None blocks from the list before appending
    mains_blocks = [b for b in mains_blocks if b is not None]

    if mains_blocks:
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✍️ Mains Ammunition"}}]}})
        blocks.extend(mains_blocks)

    # --- Prepare Properties ---
    properties = {
        "Name": {"title": [{"text": {"content": payload.get('headline', 'Untitled Topic')}}]},
        "Source URL": {"url": source_url},
        "Article Date": {"date": {"start": payload.get('article_date')}}
    }

    # Safe enum updates so they don't break if Gemini passes blank values
    if payload.get('gs_paper'):
        properties["GS Paper"] = {"select": {"name": payload['gs_paper']}}
    if payload.get('subject'):
        properties["Subject"] = {"select": {"name": payload['subject']}}

    # --- API Request ---
    try:
        notion.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=blocks
        )
        print(f"✅ [Transmitter] Successfully synced study unit: {payload.get('headline')}")
    except Exception as e:
        print(f"❌ [Transmitter] Failed to create page: {e}")
        raise e