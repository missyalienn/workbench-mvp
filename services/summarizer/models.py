from pydantic import BaseModel
from datetime import datetime


class SummarizeRequest(BaseModel):
    query: str
    plan_id: str
    posts: list[Post]
    prompt_version: str
    max_posts: int
    max_comments_per_post: int
    max_snippet_length: int
    max_comments_per_post: int