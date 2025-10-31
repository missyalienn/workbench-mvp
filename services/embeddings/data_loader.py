import json
from config.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

def load_jsonl_data(file_path: str) -> list[dict]:
    """
    Load and validate records from a .jsonl file.
    
    Each line is parsed as a JSON object and checked for required keys:
    id, text, flair, link_id, and url. Malformed, missing, or empty lines
    are logged and skipped. A summary log reports the number of valid
    records loaded.

    Returns:
        list[dict]: Valid JSONL records ready for embedding.
    """
    required_keys = {"id", "text", "flair", "link_id", "url"}
    records = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    logger.info(f"Line {line_num}: Empty line skipped.")
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Line {line_num}: JSON decode error: {e}")
                    continue
                if not isinstance(data, dict):
                    logger.warning(f"Line {line_num}: Not a JSON object, got {type(data)}")
                    continue
                missing = required_keys - data.keys()
                if missing:
                    logger.warning(f"Line {line_num}: Missing keys: {missing}")
                    continue
                records.append(data)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except OSError as e:
        logger.error(f"Error opening file '{file_path}': {e}")
        return []
    logger.info(f"Loaded {len(records)} valid records from '{file_path}'.")
    return records


if __name__ == "__main__":
    configure_logging()
    logger.info("Starting data loader runner...")
    test_path = "data/reddit_diy_baseline.jsonl"
    records = load_jsonl_data(test_path)
    logger.info(f"Runner loaded {len(records)} valid records.")

