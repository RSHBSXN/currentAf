import json
from google import genai
from google.genai import types
from src.schemas import UPSCAnalysis

def analyze_article(raw_text: str, source_url: str) -> dict:
    """
    Ingests raw news article text and uses Gemini 2.5 Pro to extract
    a highly structured, UPSC-aligned study payload based on the Pydantic schema.
    """
    print(f"🧠 [Layer 3] Analyzing raw text data with Gemini 2.5 flash...")
    
    sys_instruct = (
        "You are a Senior UPSC Mentor and elite answer-writing coach. "
        "Your objective is to distill raw news into high-yield, structured study units. "
        
        "### Step-by-Step Analysis Framework (Chain-of-Thought):"
        "1. NOISE REDUCTION: Identify the core topic. Immediately discard editorial fluff, advertisements, and repetitive journalistic rhetoric."
        "2. SYLLABUS ALIGNMENT: Mentally map the content to the official UPSC GS Paper and Subject syllabus."
        "3. FACT EXTRACTION: Isolate concrete data (dates, committees, indices, constitutional articles) for Prelims."
        "4. STRUCTURAL SYNTHESIS: Convert arguments into Mains-style points: (Issue -> Provision -> Impact/Challenge -> Way Forward)."

        "### Quality Constraints:"
        "- GS PAPER MAPPING: You MUST map the content to the exact GS Paper and Subject provided in the schema."
        "- CONCISENESS: Do not write flowery prose. Every sentence must have 'exam-value'. If a point doesn't help in an answer, drop it."
        "- DATE EXTRACTION: Extract the exact YYYY-MM-DD publication date. Fallback to 2026-06-01 only if missing."
        "- FORMAT: Your output must strictly match the UPSCAnalysis Pydantic schema."
    )
    
    try:
        client = genai.Client()
        
        config = types.GenerateContentConfig(
            system_instruction=sys_instruct,
            response_mime_type="application/json",
            response_schema=UPSCAnalysis,
            temperature=0.1 # Low temperature for analytical precision
        )
        
        # We pass both the URL and the text to give the LLM maximum context
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Source URL: {source_url}\n\nRaw Text Content:\n{raw_text}",
            config=config
        )
        
        # Parse the JSON response back into a Python dictionary
        analysis_payload = json.loads(response.text)
        print("✅ [Layer 3] Cognitive structural analysis complete.")
        return analysis_payload

    except Exception as e:
        print(f"❌ [Layer 3] Generation failed or schema validation breached: {e}")
        return None