import json 
from .content_filters import clean_text
from .fetch_data import fetch_comments
from config.logging_config import get_logger

# Initialize logger 
logger = get_logger(__name__)

#Build Dataset
def build_dataset(posts_list, comment_limit=20):
    """Build flat dataset from posts and their comments."""
    logger.info("Building dataset...")

    dataset = []
    
    for i, submission in enumerate(posts_list):
        # Get comments for this post
        comments = fetch_comments(submission, comment_limit)
        
        # Clean post title and content
        clean_title = clean_text(submission.title)
        clean_body = clean_text(submission.selftext)
        
        # Combine title and content
        title_body_text = f"{clean_title} {clean_body}".strip()
        
        # Create post record (flat structure)
        post_record = {
            'id': f"post_{submission.id}",
            'type': 'post',
            'text': title_body_text,
            'score': submission.score,
            'url': f"https://reddit.com{submission.permalink}",
            'link_id': f"post_{submission.id}",
            'flair': (getattr(submission, 'link_flair_text', '') or '').lower(),
            'len_text': len(title_body_text)
        }
        dataset.append(post_record)
        
        # Create comment records (flat structure)
        for comment in comments:
            clean_comment_text = clean_text(comment.body)
            comment_record = {
                'id': f"comment_{comment.id}",
                'type': 'comment',
                'text': clean_comment_text,
                'score': comment.score,
                'url': f"https://reddit.com{comment.permalink}",
                'link_id': f"post_{submission.id}",
                'flair': (getattr(submission, 'link_flair_text', '') or '').lower(),
                'len_text': len(clean_comment_text)
                }
            dataset.append(comment_record)
    
    logger.info( "Dataset created. Total: %d records", len(dataset))

    return dataset

def save_jsonl(dataset, filename="reddit_data.jsonl", batch_size=100):
    """Save dataset to JSONL file in batches."""
    logger.info("Saving dataset to %s in batches of %d", filename, batch_size)
    
    # Clear the file first
    with open(filename, 'w', encoding='utf-8') as f:
        pass
    
    # Process dataset in batches
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i:i + batch_size]
        
        # Append batch to file (one JSON object per line)
        with open(filename, 'a', encoding='utf-8') as f:
            for record in batch:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')  # One record per line
        
        logger.info(
            "Saved batch %d/%d (%d records)",
            i // batch_size + 1,
            (len(dataset) + batch_size - 1) // batch_size,
            len(batch),
        )
    logger.info("Dataset saved to %s. Total records: %d", filename, len(dataset))
