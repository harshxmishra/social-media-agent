import datetime
from typing import List, Literal, Optional, Union, Dict # Added Dict here

from pydantic import BaseModel, Field

# Import helper models from models.py
from .models import ComplexPost, ImageModel, YouTubeVideoSummary # Added YouTubeVideoSummary too

# --- Helper Pydantic Models ---
# Removed inline ComplexPost, ImageModel as they are imported now.
# YouTubeVideoSummary was also defined here, now imported.

# class YouTubeVideoSummary(BaseModel): # Defined in models.py
#     """Defines the structure for a YouTube video summary."""
#    link: str # These were orphaned, now removed.
#    summary: str # These were orphaned, now removed.

# Type alias for DateType from the TypeScript definition
# Using datetime.date for the Date object, and string literals for "p1", etc.
DateType = Union[datetime.date, Literal["p1", "p2", "p3", "r1", "r2", "r3"], str]
# Using str as a fallback for date string representation if not a specific literal,
# to accommodate flexibility if the TS 'Date' could also be a string date.
# For Pydantic, it's often better to be more specific or handle parsing.
# For now, datetime.date or specific literals are preferred.

# --- Main State Definition for GeneratePost ---

class GeneratePostState(BaseModel):
    """
    Represents the state of the 'generate_post' LangGraph agent.
    Derived from src/agents/generate-post/generate-post-state.ts
    """
    links: List[str] = Field(default_factory=list)

    # From IngestDataAnnotation.spec.report
    report: str = ""

    # From VerifyLinksResultAnnotation.spec
    pageContents: List[str] = Field(default_factory=list) # TS: string[] | undefined, default []
    relevantLinks: List[str] = Field(default_factory=list) # TS: string[] | undefined, default []
    imageOptions: List[str] = Field(default_factory=list) # TS: string[] | undefined, default []

    post: str = ""
    complexPost: Optional[ComplexPost] = None
    scheduleDate: Optional[DateType] = None # TS: DateType (Date | "p1" | ...)
    userResponse: Optional[str] = None

    # Renamed 'next' to 'next_node_action' to avoid Pydantic/Python keyword conflicts,
    # or could use Field(alias="next")
    # The type END from langgraph is typically represented as a specific string or just None
    # if the graph terminates. For explicit values, we use Literal.
    next_node_action: Optional[Literal[
        "schedulePost",
        "rewritePost",
        "updateScheduleDate",
        "unknownResponse",
        "rewriteWithSplitUrl",
        "END" # langgraph.END is often used in edge conditions, state might reflect this intention
    ]] = Field(default=None, alias="next")

    image: Optional[ImageModel] = None
    condenseCount: int = 0

    # For handling Arcade auth resumption
    pending_arcade_auth: Optional[Dict[str, str]] = None # e.g., {"service": "linkedin", "auth_id": "some_id"}


    class Config:
        # This allows using 'next' in the input data that maps to 'next_node_action'
        populate_by_name = True


# --- Input Schema for GeneratePost ---

class GeneratePostInput(BaseModel):
    """
    Defines the input schema for the 'generate_post' graph.
    Derived from src/agents/generate-post/generate-post-state.ts (GeneratePostInputAnnotation)
    """
    links: List[str]


# --- Configurable Fields for GeneratePost ---

# These constants are used as keys in the TypeScript configuration.
# We'll define them as Python variables for clarity if needed elsewhere,
# but Pydantic fields will match the string keys for direct mapping.
POST_TO_LINKEDIN_ORGANIZATION_KEY = "postToLinkedInOrganization"
TEXT_ONLY_MODE_KEY = "textOnlyMode"
SKIP_CONTENT_RELEVANCY_CHECK_KEY = "skipContentRelevancyCheck"
SKIP_USED_URLS_CHECK_KEY = "skipUsedUrlsCheck"

class GeneratePostConfigurable(BaseModel):
    """
    Defines the configurable fields for the 'generate_post' graph.
    Derived from src/agents/generate-post/generate-post-state.ts (GeneratePostConfigurableAnnotation)
    """
    postToLinkedInOrganization: Optional[bool] = Field(default=None, alias=POST_TO_LINKEDIN_ORGANIZATION_KEY)
    textOnlyMode: bool = Field(default=False, alias=TEXT_ONLY_MODE_KEY) # TS default is false
    origin: Optional[str] = None
    skipContentRelevancyCheck: Optional[bool] = Field(default=None, alias=SKIP_CONTENT_RELEVANCY_CHECK_KEY)
    skipUsedUrlsCheck: Optional[bool] = Field(default=None, alias=SKIP_USED_URLS_CHECK_KEY)

    class Config:
        # Allows using the TypeScript style keys in input data
        populate_by_name = True

# Example of how langgraph.END might be used, for context.
# from langgraph.graph import END as LANGGRAPH_END
# next_node_action: Optional[Literal["schedulePost", ..., LANGGRAPH_END]]

# Placeholder for LangChainProduct if needed by nodes, not directly in GeneratePostState
LangChainProduct = Literal["langchain", "langgraph", "langsmith"]
