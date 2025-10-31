from typing import Optional, Sequence

from config.logging_config import configure_logging, get_logger

from .build_dataset import build_dataset, save_jsonl
from .fetch_data import fetch_posts
from .reddit_client import get_reddit_client

logger = get_logger(__name__)


def run_ingestion(
    limit: int = 50,
    comment_limit: int = 4,
    save_path: Optional[str] = None,
    reddit_client=None,
) -> Sequence[dict]:
    """Execute the ingestion pipeline end-to-end."""
    configure_logging()
    client = reddit_client or get_reddit_client()

    logger.info("Starting ingestion run (limit=%d, comment_limit=%d)", limit, comment_limit)

    posts = fetch_posts(client, limit=limit)
    if not posts:
        logger.warning("No posts fetched; skipping dataset build.")
        return []

    dataset = build_dataset(posts, comment_limit=comment_limit)
    logger.info("Dataset assembled with %d records", len(dataset))

    if save_path:
        logger.info("Persisting dataset to %s", save_path)
        save_jsonl(dataset, filename=save_path)

    logger.info("Ingestion run complete")
    return dataset

# To run ingestion pipeline AND generate a new jsonl file: pass save_path to run_ingestion() 
# Ex: run_ingestion(save_path = "data/new_json_file.jsonl")

if __name__ == "__main__":
    run_ingestion (save_path="data/reddit_diy_baseline.jsonl") 
