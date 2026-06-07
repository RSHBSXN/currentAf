import json
from google import genai
from google.genai import types
from src.schemas import UPSCAnalysis

def analyze_article(raw_text: str, source_url: str) -> dict:
    """
    Ingests raw news article text and uses Gemini 2.5 Pro to filter for 
    UPSC relevance and extract a high-yield, tutor-style study payload.
    """
    print(f"🧠 [Layer 2] Analyzing text with Gemini 2.5 Pro (Tutor & Gatekeeper)...")
    
    sys_instruct = (
        "You are an expert, patient UPSC Tutor and elite answer-writing coach preparing a student for the 2026 exam. "
        "Your objective is to evaluate raw news text, filter out noise, and distill relevant articles into high-yield study notes.\n\n"
        
        "### Step 1: SYLLABUS GATEKEEPER (Critical)\n"
        "Determine if the content directly impacts the official UPSC CSE Syllabus (GS-1, GS-2, GS-3, GS-4) or core current affairs. "
        "If it is irrelevant (e.g., local crime, sports, celebrity gossip, pure party-political drama), "
        "set 'is_upsc_relevant' to False and you may leave other fields blank or empty.\n\n"
        
        "### Step 2: TUTOR-STYLE BREAKDOWN (If Relevant)\n"
        "If relevant, set 'is_upsc_relevant' to True and fulfill the schema fields with maximum exam value:\n"
        "- headline: A clean, academic title for the topic.\n"
        "- gs_paper & subject: Select the exact matching enum value that fits the core theme.\n"
        "- syllabus_topics: List explicit keywords or syllabus headers from the official UPSC syllabus.\n"
        "- core_context: Write a multi-paragraph, plain-English explanation breaking down the background, the 'Why', and the 'How' of the issue. Avoid dense jargon.\n"
        "- official_citations: Extract specific constitutional articles, landmark Supreme Court cases, central ministries, or statutory committees.\n"
        "- prelims_facts: Isolate core factual nuggets crucial for Prelims (e.g., species IUCN status, indexing bodies, geographic locations).\n"
        "- key_arguments: Format structural dimensions of the issue (e.g., institutional bottlenecks, socio-economic impacts) as crisp bullet points perfect for Mains.\n"
        "- way_forward: Provide constructive, actionable, policy-driven solutions suitable for a Mains conclusion.\n"
        "- mains_case_study: Synthesize how the student can deploy this specific event as an illustrative example or case study in a Mains answer.\n\n"
        
        "### Quality Constraints:\n"
        "- Every sentence must hold distinct 'exam-value'. Avoid flowery filler prose.\n"
        "- Your JSON output MUST strictly validate against the requested UPSCAnalysis Pydantic schema."
    )
    
    try:
        client = genai.Client()
        
        config = types.GenerateContentConfig(
            system_instruction=sys_instruct,
            response_mime_type="application/json",
            response_schema=UPSCAnalysis,
            temperature=0.2 # Lower temperature ensures strict analytical precision
        )
        
        # Pass the cleaned text to Gemini 2.5 Pro
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=f"Source URL: {source_url}\n\nRaw Text Content:\n{raw_text}",
            config=config
        )
        
        # Parse the JSON response back into a Python dictionary
        analysis_payload = json.loads(response.text)
        print("✅ [Layer 2] Cognitive structural analysis complete.")
        return analysis_payload

    except Exception as e:
        print(f"❌ [Layer 2] Generation failed or schema validation breached: {e}")
        return None