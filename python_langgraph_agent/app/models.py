from typing import List, Optional, Union # Added Union for DateType if we move it too
import datetime # For DateType if we move it too
from pydantic import BaseModel, Field # Field might be useful if adding defaults here

# --- General Helper Models (moved from state.py) ---

class ComplexPost(BaseModel):
    """Defines the structure for a post split into a main post and a reply."""
    main_post: str
    reply_post: str

class ImageModel(BaseModel):
    """Defines the structure for an image to be attached to a post."""
    imageUrl: str # Field names can be converted to snake_case if preferred, using alias
    mimeType: str

class YouTubeVideoSummary(BaseModel):
    """Defines the structure for a YouTube video summary."""
    link: str
    summary: str


# --- Models for Reddit Data ---

class SimpleRedditCommentModel(BaseModel):
    id: str
    author: str
    body: str
    created_utc: int # Assuming timestamp as integer
    score: Optional[int] = None # Added score as it's in RedditCommentData
    replies: Optional[List['SimpleRedditCommentModel']] = None

# Call model_rebuild() to resolve forward references for replies
SimpleRedditCommentModel.model_rebuild()


class SimpleRedditPostModel(BaseModel):
    id: str
    title: str
    url: str
    selftext: str # Text content of the post
    created_utc: int # Assuming timestamp as integer


class SimpleRedditPostWithCommentsModel(BaseModel):
    post: SimpleRedditPostModel
    comments: List[SimpleRedditCommentModel]


# --- Input Models for Verification Nodes/Subgraphs ---

class VerifyContentInput(BaseModel):
    """
    Input for general content verification nodes.
    Corresponds to VerifyContentAnnotation in TS.
    """
    link: str


class VerifyRedditPostInput(BaseModel):
    """
    Input for the Reddit post verification subgraph.
    Corresponds to parts of VerifyRedditPostAnnotation in TS.
    """
    link: Optional[str] = None
    postID: Optional[str] = None # 'postID' from TS
    redditPost: Optional[SimpleRedditPostWithCommentsModel] = None

    # Ensure at least one identifier is provided (can be done with a root_validator if needed)
    # @root_validator(pre=True)
    # def check_at_least_one_identifier(cls, values):
    #     if not any(values.get(key) for key in ['link', 'postID', 'redditPost']):
    #         raise ValueError('Either link, postID, or redditPost must be provided')
    #     return values

# --- Other specific input/output models can be added here as needed ---
