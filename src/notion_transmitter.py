import os
from notion_client import Client

def transmit_to_notion(payload: dict, source_url: str, youtube_url: str):
    """
    Transmits the parsed analysis payload into the Notion database.
    """
    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_DATABASE_ID")

    # Helper: Create standard bullet points
    def bullet(text):
        return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

    # Helper: Create Toggles for Mains content
    def toggle(title, items):
        return {
            "object": "block", "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": title}, "annotations": {"bold": True}}],
                "children": [bullet(item) for item in items]
            }
        }

    # Construct the Page Blocks
    blocks = [
        # YouTube Link
        {"object": "block", "type": "callout", "callout": {
            "rich_text": [{"type": "text", "text": {"content": "🎥 Concept Briefing: "}, "annotations": {"bold": True}}, 
                          {"type": "text", "text": {"content": "Find Lecture on YouTube", "link": {"url": youtube_url}}}],
            "icon": {"type": "emoji", "emoji": "💡"}
        }},
        # Core Context
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": payload['core_context']}}]}},
        # Prelims Heading
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🎯 Prelims Pillars"}}]}},
        *[bullet(f) for f in payload['prelims_facts']],
        # Mains Heading
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✍️ Mains Ammunition"}}]}},
        toggle("Key Arguments", payload['key_arguments']),
        toggle("Way Forward", payload['way_forward']),
        toggle("Case Study", [payload['mains_case_study']])
    ]

    # API Request
    try:
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {"title": [{"text": {"content": payload['headline']}}]},
                "GS Paper": {"select": {"name": payload['gs_paper']}},
                "Subject": {"select": {"name": payload['subject']}},
                "Source URL": {"url": source_url},
                "Article Date": {
                    "date": {"start": payload['article_date']}
                }
            },
            children=blocks
        )
        print(f"✅ [Transmitter] Successfully synced: {payload['headline']}")
    except Exception as e:
        print(f"❌ [Transmitter] Failed: {e}")