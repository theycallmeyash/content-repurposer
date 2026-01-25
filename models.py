from pydantic import BaseModel, Field
from typing import List, Optional

class Tweet(BaseModel):
    content: str = Field(..., description="The content of the tweet. Must be under 280 characters.")

class TwitterThread(BaseModel):
    tweets: List[Tweet] = Field(..., description="A list of tweets forming a thread.")

class LinkedInPost(BaseModel):
    content: str = Field(..., description="Professional LinkedIn post content.")

class InstagramCaption(BaseModel):
    content: str = Field(..., description="Instagram caption content.")
    hashtags: List[str] = Field(..., description="List of relevant hashtags.")

class CoreAnalysis(BaseModel):
    summary: str = Field(..., description="Executive summary of the content.")
    key_points: List[str] = Field(..., description="List of key takeaways.")
    tone: str = Field(..., description="Detected tone of the content.")
    audience: str = Field(..., description="Target audience analysis.")

class RepurposedContent(BaseModel):
    core_analysis: CoreAnalysis
    twitter_thread: TwitterThread
    linkedin_post: LinkedInPost
    instagram_caption: InstagramCaption
    tldr: str = Field(..., description="A very short TL;DR summary.")
