"""Reddit tools for the research graph.

Provides:
  - reddit_fetch_node: LangGraph node that runs the planner + fetcher once and
    stores the resulting post corpus in GraphState.
  - search_reddit_corpus: plain function that re-ranks the shared corpus against
    a dimension-specific query using cosine similarity.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from agent.clients.openai_client import get_openai_client
from agent.planner.core import create_search_plan
from config.logging_config import get_logger
from config.settings import settings
from services.embedding.client import EmbeddingClient
from services.embedding.similarity import cosine_similarity
from services.embedding.store_factory import get_vector_store
from services.fetch.reddit_fetcher import run_reddit_fetcher
from services.fetch.schemas import Post

if TYPE_CHECKING:
    from graph.schemas import GraphState

logger = get_logger(__name__)

_TOP_N_DEFAULT = 5


def _build_embedder() -> EmbeddingClient:
    return EmbeddingClient(
        client=get_openai_client(),
        model=settings.EMBEDDING_MODEL,
        store=get_vector_store(),
    )


def search_reddit_corpus(
    query: str,
    posts: list[Post],
    *,
    top_n: int = _TOP_N_DEFAULT,
) -> str:
    """Re-rank the shared Reddit corpus against a dimension-specific query.

    Returns a formatted string of the top-N posts and their comments,
    suitable for passing directly into an agent's message context.
    """
    if not posts:
        return "No Reddit posts available in corpus."

    embedder = _build_embedder()

    query_vector, _ = embedder.embed(query)

    post_texts = [f"{p.title}\n\n{p.selftext}" for p in posts]
    post_vectors = embedder.embed_texts(post_texts)

    scored: list[tuple[float, Post]] = []
    for post, vector in zip(posts, post_vectors):
        score = cosine_similarity(query_vector, vector) if vector is not None else 0.0
        scored.append((score, post))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_n]

    lines: list[str] = []
    for rank, (score, post) in enumerate(top, start=1):
        lines.append(f"[{rank}] {post.title} (r/{post.subreddit}, score={score:.3f})")
        lines.append(f"URL: {post.url}")
        if post.selftext.strip():
            lines.append(post.selftext[:500])
        for comment in post.comments[:3]:
            lines.append(f"  > {comment.body[:300]}")
        lines.append("")

    return "\n".join(lines)


async def reddit_fetch_node(state: GraphState) -> dict[str, Any]:
    """LangGraph node: run planner + fetcher once and store corpus in state.

    Wraps the synchronous pipeline stages in asyncio.to_thread so the graph
    stays async without rewriting the existing fetch internals.
    """
    brief = state["brief"]
    if brief is None:
        raise ValueError("reddit_fetch_node requires brief to be set in state.")

    logger.info("reddit_fetch_node.start", fetch_query=brief.fetch_query)

    plan = await asyncio.to_thread(
        create_search_plan,
        brief.fetch_query,
        model=settings.PLANNER_MODEL,
    )

    fetch_result = await asyncio.to_thread(
        run_reddit_fetcher,
        plan,
        post_limit=settings.FETCHER_POST_LIMIT,
    )


    logger.info("reddit_fetch_node.complete", n_posts=len(fetch_result.posts))

    return {"reddit_posts": fetch_result.posts}
