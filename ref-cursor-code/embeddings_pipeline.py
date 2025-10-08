#!/usr/bin/env python3
"""
Embeddings Pipeline for Reddit Data
Generates embeddings using OpenAI and stores them in Pinecone vector database.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import openai
from pinecone import Pinecone, ServerlessSpec
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API credentials from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'reddit-diy-embeddings')

# Initialize OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    logger.error("OPENAI_API_KEY not found in environment variables")

# Initialize Pinecone client
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
else:
    logger.error("PINECONE_API_KEY not found in environment variables")
    pc = None

def create_retry_session(max_retries=3, backoff_factor=1):
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def generate_embeddings(jsonl_file: str, batch_size: int = 100) -> List[Tuple[str, List[float], Dict[str, Any]]]:
    """
    Reads JSONL file, generates embeddings with OpenAI, returns list of vectors.
    
    Args:
        jsonl_file: Path to JSONL file containing Reddit data
        batch_size: Number of records to process in each batch
        
    Returns:
        List of tuples: (id, embedding_vector, metadata)
    """
    logger.info(f"Generating embeddings from {jsonl_file}")
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    vectors_list = []
    batch = []
    total_processed = 0
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    batch.append(record)
                    
                    # Process batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        batch_vectors = _process_batch(batch, line_num)
                        vectors_list.extend(batch_vectors)
                        total_processed += len(batch)
                        logger.info(f"Processed {total_processed} records...")
                        batch = []
                        
                        # Rate limiting - OpenAI has rate limits
                        time.sleep(0.1)  # Small delay between batches
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON on line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    continue
            
            # Process remaining records in final batch
            if batch:
                batch_vectors = _process_batch(batch, line_num)
                vectors_list.extend(batch_vectors)
                total_processed += len(batch)
        
        logger.info(f"Successfully generated embeddings for {total_processed} records")
        return vectors_list
        
    except FileNotFoundError:
        logger.error(f"File {jsonl_file} not found")
        raise
    except Exception as e:
        logger.error(f"Error reading file {jsonl_file}: {e}")
        raise

def _process_batch(batch: List[Dict[str, Any]], line_num: int) -> List[Tuple[str, List[float], Dict[str, Any]]]:
    """Process a batch of records and generate embeddings."""
    batch_vectors = []
    
    for record in batch:
        try:
            # Prepare text for embedding
            text = record.get('text', '')
            if not text:
                logger.warning(f"Empty text for record {record.get('id', 'unknown')}")
                continue
            
            # Generate embedding with retry logic
            embedding = _generate_embedding_with_retry(text)
            
            # Prepare metadata
            metadata = {
                'type': record.get('type', ''),
                'score': record.get('score', 0),
                'source': record.get('source', 'reddit'),
                'created_at': record.get('created_at', 0),
                'text': text[:1000]  # Truncate for Pinecone metadata limits
            }
            
            # Add post-specific metadata
            if record.get('type') == 'post':
                metadata['url'] = record.get('url', '')
            elif record.get('type') == 'comment':
                metadata['link_id'] = record.get('link_id', '')
            
            batch_vectors.append((record['id'], embedding, metadata))
            
        except Exception as e:
            logger.error(f"Error processing record {record.get('id', 'unknown')}: {e}")
            continue
    
    return batch_vectors

def _generate_embedding_with_retry(text: str, max_retries: int = 3) -> List[float]:
    """Generate embedding with retry logic for rate limiting."""
    for attempt in range(max_retries):
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
            
        except openai.RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 1  # Exponential backoff
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                time.sleep(wait_time)
            else:
                logger.error(f"Rate limit exceeded after {max_retries} attempts")
                raise
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Error generating embedding, retrying: {e}")
                time.sleep(1)
            else:
                logger.error(f"Failed to generate embedding after {max_retries} attempts: {e}")
                raise

def upsert_to_pinecone(vectors_list: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
    """
    Upserts embedding vectors into Pinecone index.
    
    Args:
        vectors_list: List of tuples (id, embedding_vector, metadata)
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Upserting {len(vectors_list)} vectors to Pinecone")
    
    if not pc:
        raise ValueError("Pinecone client not initialized - check PINECONE_API_KEY")
    
    try:
        # Check if index exists, create if not
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            logger.info(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=1536,  # text-embedding-3-small dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=PINECONE_ENVIRONMENT
                )
            )
            # Wait for index to be ready
            time.sleep(10)
        
        # Get index
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Prepare vectors for upsert
        vectors_to_upsert = []
        for vector_id, embedding, metadata in vectors_list:
            vectors_to_upsert.append({
                'id': vector_id,
                'values': embedding,
                'metadata': metadata
            })
        
        # Upsert in batches (Pinecone has batch size limits)
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            index.upsert(vectors=batch)
            logger.info(f"Upserted batch {i//batch_size + 1}/{(len(vectors_to_upsert) + batch_size - 1)//batch_size}")
            
            # Small delay between batches
            time.sleep(0.1)
        
        logger.info(f"Successfully upserted {len(vectors_list)} vectors to Pinecone")
        return True
        
    except Exception as e:
        logger.error(f"Error upserting to Pinecone: {e}")
        return False

def main():
    """Main function to run the embeddings pipeline."""
    logger.info("Starting embeddings pipeline...")
    
    # Check for required environment variables
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return
    
    if not PINECONE_API_KEY:
        logger.error("PINECONE_API_KEY not found in environment variables")
        return
    
    # Check if JSONL file exists
    jsonl_file = "reddit_data.jsonl"
    if not os.path.exists(jsonl_file):
        logger.error(f"JSONL file {jsonl_file} not found. Run ingest-pipeline.py first.")
        return
    
    try:
        # Generate embeddings
        vectors_list = generate_embeddings(jsonl_file)
        
        if not vectors_list:
            logger.error("No vectors generated")
            return
        
        # Upsert to Pinecone
        success = upsert_to_pinecone(vectors_list)
        
        if success:
            logger.info("Embeddings pipeline completed successfully!")
        else:
            logger.error("Embeddings pipeline failed")
            
    except Exception as e:
        logger.error(f"Embeddings pipeline failed: {e}")

if __name__ == "__main__":
    main()