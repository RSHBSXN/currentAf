from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class GSPaperEnum(str, Enum):
    GS1 = "GS-1"
    GS2 = "GS-2"
    GS3 = "GS-3"
    GS4 = "GS-4"
    PRELIMS = "Prelims Only"

class SubjectEnum(str, Enum):
    MISC = "Miscellaneous"
    ETHICS = "Ethics"
    AGRICULTURE = "Agriculture"
    INTERNAL_SECURITY = "Internal Security"
    DISASTER_MGMT = "Disaster Management"
    ENVIRONMENT = "Environment"
    SCI_TECH = "Science & Technology"
    SOCIAL_JUSTICE = "Social Justice"
    IR = "International Relations"
    GOVERNANCE = "Governance"
    SOCIETY = "Society"
    GEOGRAPHY = "Geography"
    HIST_ART_CULTURE = "History - Art & Culture"
    HIST_MODERN = "History - Modern"
    HIST_MEDIEVAL = "History - Medieval"
    HIST_ANCIENT = "History - Ancient"
    POLITY = "Polity"
    ECONOMY = "Economy"

class UPSCAnalysis(BaseModel):
    # --- THE SYLLABUS GATEKEEPER ---
    is_upsc_relevant: bool = Field(
        description="True ONLY if the article directly impacts the official UPSC CSE Syllabus (GS 1, 2, 3, 4) or Core Current Affairs. Set to False for local crime, sports, regional updates, or celebrity gossip."
    )
    
    # All other fields are wrapped as Optional or given an empty default list.
    # This ensures that if is_upsc_relevant is False, the model can safely skip them.
    headline: Optional[str] = Field(default=None, description="A clean, academic title for the topic.")
    
    # --- Tiered Taxonomy (Zone 1) ---
    gs_paper: Optional[GSPaperEnum] = None
    subject: Optional[SubjectEnum] = None
    syllabus_topics: list[str] = Field(default_factory=list, description="Explicit keywords from the official UPSC syllabus.")
    
    # --- Core Context & Citations (Zone 1) ---
    core_context: Optional[str] = Field(
        default=None, 
        description="A detailed, patient breakdown explaining the 'Why' and 'How' of the issue. Break down background and technical jargon in plain English so a student can easily grasp it."
    )
    official_citations: list[str] = Field(default_factory=list, description="Names of any official committees, government reports, global indices, or constitutional articles mentioned. (e.g., 'Gadgil Committee Report', 'Article 21').")
    
    # --- Prelims Radar (Zone 2) ---
    prelims_facts: list[str] = Field(default_factory=list, description="Core factual nuggets crucial for Prelims (e.g., species status, indices publishers, geographical locations, constitutional amendments).")
    
    # --- Mains Ammunition (Zone 3) ---
    key_arguments: list[str] = Field(default_factory=list, description="The structural dimensions of the issue (e.g., institutional bottlenecks, socio-economic impacts).")
    way_forward: list[str] = Field(default_factory=list, description="Actionable, policy-driven solutions.")
    mains_case_study: Optional[str] = Field(default=None, description="How a student can use this as a real-world example in a Mains answer.")