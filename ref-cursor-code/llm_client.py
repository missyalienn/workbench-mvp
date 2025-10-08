#!/usr/bin/env python3
"""
LLM Client for OpenAI Operations
Handles all OpenAI API interactions including embeddings and chat completions.
"""

import os
import time
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    logger.error("OPENAI_API_KEY not found in environment variables")

def generate_embedding(text: str, model: str = "text-embedding-3-small", max_retries: int = 3) -> List[float]:
    """
    Generate embedding for text using OpenAI API with retry logic.
    
    Args:
        text: Text to embed
        model: OpenAI embedding model to use
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of embedding values
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    for attempt in range(max_retries):
        try:
            response = openai.embeddings.create(
                model=model,
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

def generate_chat_completion(messages: List[Dict[str, str]], model: str = "gpt-4o-mini", max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """
    Generate chat completion using OpenAI API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: OpenAI model to use
        max_tokens: Maximum tokens in response
        temperature: Response creativity (0.0 to 1.0)
        
    Returns:
        Generated response text
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
        
    except openai.RateLimitError as e:
        logger.error(f"OpenAI rate limit exceeded: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating chat completion: {e}")
        raise

def format_context_for_llm(search_results: List[Dict[str, Any]]) -> str:
    """
    Formats search results into context for LLM input.
    
    Args:
        search_results: List of search results from semantic search
        
    Returns:
        Formatted context string
    """
    if not search_results:
        return "No relevant context found."
    
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_part = f"[Source {i}: {result['id']}]\n"
        context_part += f"Type: {result['type']}\n"
        context_part += f"Text: {result['text']}\n"
        context_part += f"Relevance Score: {result['score']:.3f}\n"
        
        if result.get('url'):
            context_part += f"URL: {result['url']}\n"
        
        context_parts.append(context_part)
    
    return "\n---\n".join(context_parts)

def create_rag_messages(user_question: str, context: str) -> List[Dict[str, str]]:
    """
    Create properly formatted messages for RAG chat completion.
    
    Args:
        user_question: User's question
        context: Formatted context from search results
        
    Returns:
        List of message dictionaries for OpenAI API
    """
    system_prompt = """You are an assistant answering DIY questions using Reddit discussions as context. 
    Use the provided context to give helpful, accurate answers. Always cite your sources using the format [source: post_id].
    If the context doesn't contain enough information to answer the question, say so clearly.
    Keep your answers concise but comprehensive."""
    
    user_message = f"""Context from Reddit discussions:
    
{context}

Question: {user_question}

Please provide a helpful answer based on the context above. Include citations using [source: post_id] format."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
