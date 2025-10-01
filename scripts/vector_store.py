#!/usr/bin/env python3
"""
Vector Store Operations for Pinecone
Handles all Pinecone database operations including semantic search.
"""

import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Pinecone configuration
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'reddit-diy-embeddings')

# Initialize Pinecone client
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
else:
    logger.error("PINECONE_API_KEY not found in environment variables")
    pc = None

def init_pinecone() -> bool:
    """
    Initialize Pinecone connection and verify index exists.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not pc:
        logger.error("Pinecone client not initialized")
        return False
    
    try:
        # Check if index exists
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            logger.error(f"Index {PINECONE_INDEX_NAME} not found")
            return False
        
        logger.info(f"Successfully connected to Pinecone index: {PINECONE_INDEX_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing Pinecone: {e}")
        return False

def semantic_search(query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Performs semantic search on Pinecone index using query embedding.
    
    Args:
        query_embedding: Vector embedding of the query
        top_k: Number of top results to return
        
    Returns:
        List of search results with metadata
    """
    logger.info(f"Performing semantic search with top_k={top_k}")
    
    if not pc:
        raise ValueError("Pinecone client not initialized - check PINECONE_API_KEY")
    
    try:
        # Get Pinecone index
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Search for similar vectors
        search_results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results
        formatted_results = []
        for match in search_results.matches:
            result = {
                'id': match.id,
                'score': match.score,
                'text': match.metadata.get('text', ''),
                'type': match.metadata.get('type', ''),
                'source': match.metadata.get('source', 'reddit'),
                'score_original': match.metadata.get('score', 0),
                'created_at': match.metadata.get('created_at', 0)
            }
            
            # Add type-specific metadata
            if match.metadata.get('type') == 'post':
                result['url'] = match.metadata.get('url', '')
            elif match.metadata.get('type') == 'comment':
                result['link_id'] = match.metadata.get('link_id', '')
            
            formatted_results.append(result)
        
        logger.info(f"Found {len(formatted_results)} relevant results")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise

def upsert_embeddings(embeddings: List[tuple], index_name: str = None) -> bool:
    """
    Upserts embeddings into Pinecone index.
    
    Args:
        embeddings: List of tuples (id, embedding_vector, metadata)
        index_name: Name of the index (uses default if None)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if index_name is None:
        index_name = PINECONE_INDEX_NAME
    
    logger.info(f"Upserting {len(embeddings)} vectors to Pinecone index: {index_name}")
    
    if not pc:
        raise ValueError("Pinecone client not initialized - check PINECONE_API_KEY")
    
    try:
        # Get index
        index = pc.Index(index_name)
        
        # Prepare vectors for upsert
        vectors_to_upsert = []
        for vector_id, embedding, metadata in embeddings:
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
        
        logger.info(f"Successfully upserted {len(embeddings)} vectors to Pinecone")
        return True
        
    except Exception as e:
        logger.error(f"Error upserting to Pinecone: {e}")
        return False
