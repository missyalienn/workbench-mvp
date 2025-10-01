#!/usr/bin/env python3
"""
RAG Orchestrator
High-level coordination of RAG pipeline components.
"""

import logging
from typing import List, Dict, Any
from vector_store import semantic_search, init_pinecone
from llm_client import generate_embedding, generate_chat_completion, format_context_for_llm, create_rag_messages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def answer_query(user_question: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Performs complete RAG pipeline: retrieve relevant context and generate answer.
    
    Args:
        user_question: User's question
        top_k: Number of relevant results to retrieve
        
    Returns:
        Dictionary containing answer and sources
    """
    logger.info(f"Answering query: {user_question}")
    
    try:
        # Step 1: Generate query embedding
        query_embedding = generate_embedding(user_question)
        
        # Step 2: Perform semantic search
        search_results = semantic_search(query_embedding, top_k=top_k)
        
        if not search_results:
            return {
                'answer': "I couldn't find any relevant information to answer your question.",
                'sources': [],
                'context_used': False
            }
        
        # Step 3: Format context for LLM
        context = format_context_for_llm(search_results)
        
        # Step 4: Create messages for chat completion
        messages = create_rag_messages(user_question, context)
        
        # Step 5: Generate answer using OpenAI
        answer = generate_chat_completion(messages)
        
        # Step 6: Extract sources from the answer
        sources = _extract_sources_from_answer(answer, search_results)
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': True,
            'total_sources_found': len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Error answering query: {e}")
        return {
            'answer': "I encountered an error while processing your question. Please try again.",
            'sources': [],
            'context_used': False,
            'error': str(e)
        }

def _extract_sources_from_answer(answer: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract sources that were actually used in the answer.
    
    Args:
        answer: Generated answer text
        search_results: Original search results
        
    Returns:
        List of sources that were cited in the answer
    """
    sources = []
    for result in search_results:
        if f"[source: {result['id']}]" in answer or f"[Source {search_results.index(result) + 1}" in answer:
            sources.append({
                'id': result['id'],
                'type': result['type'],
                'text': result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
                'score': result['score'],
                'url': result.get('url', '')
            })
    return sources

def main():
    """Main function to test the RAG orchestrator."""
    logger.info("Starting RAG orchestrator test...")
    
    # Initialize Pinecone connection
    if not init_pinecone():
        logger.error("Failed to initialize Pinecone connection")
        return
    
    # Test query
    test_query = "What's the best way to strip paint from wood?"
    
    try:
        result = answer_query(test_query)
        
        print(f"\nQuestion: {test_query}")
        print(f"\nAnswer: {result['answer']}")
        
        if result['sources']:
            print(f"\nSources used:")
            for i, source in enumerate(result['sources'], 1):
                print(f"{i}. {source['type']} (ID: {source['id']})")
                print(f"   Score: {source['score']:.3f}")
                print(f"   Text: {source['text']}")
                if source.get('url'):
                    print(f"   URL: {source['url']}")
                print()
        
        logger.info("RAG orchestrator test completed successfully!")
        
    except Exception as e:
        logger.error(f"RAG orchestrator test failed: {e}")

if __name__ == "__main__":
    main()
