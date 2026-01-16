from __future__ import annotations

from .models import PostPayload, EvidenceRequest
from services.selector.config import SelectorConfig
from services.summarizer.config import EvidenceOutputConfig
from services.fetch.schemas import Comment, FetchResult, Post

from config.logging_config import get_logger

logger = get_logger(__name__)

def select_posts(fetch_result: FetchResult, cfg: SelectorConfig) -> list[Post]: 
    """
    Select top posts from a FetchResult to include in LLM summarization context.
    Ranks posts (by relevance_score then post_karma) and returns up to cfg.max_posts. 
    Does not mutate posts or truncate fields; comments remainattached for downstream usage.
    """
    ranked_posts: list[Post] = list(fetch_result.posts or [])

    ranked_posts.sort(key=lambda post: post.post_karma or 0, reverse=True)
    ranked_posts.sort(key=lambda post: post.relevance_score or 0.0, reverse=True)

    return ranked_posts[: cfg.max_posts]
    
def build_comment_excerpts(comments: list[Comment], cfg: SelectorConfig) -> list[str]: 
    """
    Select and truncate comment bodies for summarization. Take a list of Comment objects, 
    sort by comment_karma descending and truncate to cfg.max_comment_chars.
    Return a list of truncated comment bodies.
    """
    if not comments:
        return []

    ranked: list[Comment] = sorted(
        comments,
        key=lambda comment: comment.comment_karma or 0,
        reverse=True,
    )

    selected_comments = ranked[: cfg.max_comments_per_post]
    char_limit = cfg.max_comment_chars

    excerpts: list[str] = []
    for comment in selected_comments:
        body = comment.body or ""
        if len(body) > char_limit:
            excerpts.append(body[:char_limit])
        else:
            excerpts.append(body)
    return excerpts

def build_post_payload(post: Post, cfg: SelectorConfig) -> PostPayload:
    """Build a PostPayload from a single Post object."""

    full_body = post.selftext or ""
    char_limit = cfg.max_post_chars
    if len(full_body) > char_limit:
        body_excerpt = full_body[:char_limit]
    else:
        body_excerpt = full_body

    top_comment_excerpts = build_comment_excerpts(post.comments, cfg)
    subreddit = post.subreddit

    return PostPayload(
        post_id=post.id,
        subreddit=subreddit,
        title=post.title,
        url=post.url,
        body_excerpt=body_excerpt,
        top_comment_excerpts=top_comment_excerpts,
        post_karma=post.post_karma,
        num_comments=len(post.comments),
        relevance_score=post.relevance_score,
        matched_keywords=post.matched_keywords,
    )

def build_summarize_request(
    fetch_result: FetchResult,
    cfg: SelectorConfig,
    prompt_version: str,
    summarizer_cfg: EvidenceOutputConfig,
) -> EvidenceRequest:
    """
    Build a SummarizeRequest DTO from a FetchResult.

    - Selects top posts via select_posts.
    - Builds PostPayload objects for each selected post.
    - Attaches query/plan_id, prompt version, selector config metadata, and summarizer limits.
    """
    selected_posts = select_posts(fetch_result, cfg)
    post_payloads = [build_post_payload(post, cfg) for post in selected_posts]

    return EvidenceRequest(
        query=fetch_result.query,
        plan_id=fetch_result.plan_id,
        post_payloads=post_payloads,
        prompt_version=prompt_version,
        max_posts=cfg.max_posts,
        max_comments_per_post=cfg.max_comments_per_post,
        max_post_chars=cfg.max_post_chars,
        max_comment_chars=cfg.max_comment_chars,
        summary_char_budget=summarizer_cfg.summary_char_budget,
        max_highlights=summarizer_cfg.max_highlights,
        max_cautions=summarizer_cfg.max_cautions,
    )
