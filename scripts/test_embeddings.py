#!/usr/bin/env python3
"""
Test script for the embeddings pipeline.
"""

import os
import json
import tempfile
from embeddings_pipeline import generate_embeddings, upsert_to_pinecone

def create_test_jsonl():
    """Create a small test JSONL file."""
    test_data = [
        {
            "id": "post_test1",
            "type": "post",
            "text": "How to build a simple bookshelf with basic tools",
            "score": 150,
            "source": "reddit",
            "url": "https://reddit.com/r/DIY/comments/test1/",
            "created_at": 1705312200.0
        },
        {
            "id": "comment_test1",
            "type": "comment",
            "text": "Great tutorial! What type of wood did you use?",
            "score": 25,
            "link_id": "post_test1",
            "source": "reddit",
            "created_at": 1705315800.0
        },
        {
            "id": "post_test2",
            "type": "post",
            "text": "DIY coffee table made from reclaimed wood",
            "score": 89,
            "source": "reddit",
            "url": "https://reddit.com/r/DIY/comments/test2/",
            "created_at": 1705320000.0
        }
    ]
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for record in test_data:
            json.dump(record, f)
            f.write('\n')
        return f.name

def test_embeddings_generation():
    """Test embedding generation without Pinecone."""
    print("🧪 Testing embedding generation...")
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Set OPENAI_API_KEY in your .env file to test embedding generation")
        return False
    
    # Create test file
    test_file = create_test_jsonl()
    print(f"✅ Created test file: {test_file}")
    
    try:
        # Test embedding generation
        vectors_list = generate_embeddings(test_file, batch_size=2)
        
        if not vectors_list:
            print("❌ No vectors generated")
            return False
        
        print(f"✅ Generated {len(vectors_list)} embeddings")
        
        # Validate vector structure
        for i, (vector_id, embedding, metadata) in enumerate(vectors_list):
            if not isinstance(embedding, list) or len(embedding) != 1536:
                print(f"❌ Invalid embedding dimension for vector {i}")
                return False
            
            if not isinstance(metadata, dict):
                print(f"❌ Invalid metadata type for vector {i}")
                return False
            
            print(f"   Vector {i+1}: {vector_id} - {len(embedding)} dimensions")
        
        print("✅ All embeddings validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing embeddings: {e}")
        return False
    finally:
        # Clean up test file
        os.unlink(test_file)

def test_pinecone_connection():
    """Test Pinecone connection without upserting."""
    print("🧪 Testing Pinecone connection...")
    
    # Check for Pinecone API key
    if not os.getenv('PINECONE_API_KEY'):
        print("❌ PINECONE_API_KEY not found in environment variables")
        print("   Set PINECONE_API_KEY in your .env file to test Pinecone connection")
        return False
    
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        # List indexes to test connection
        indexes = pc.list_indexes()
        print(f"✅ Connected to Pinecone - found {len(indexes)} indexes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Pinecone: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Embeddings Pipeline...")
    print("=" * 50)
    
    # Test embedding generation
    embeddings_ok = test_embeddings_generation()
    print()
    
    # Test Pinecone connection
    pinecone_ok = test_pinecone_connection()
    print()
    
    # Summary
    print("=" * 50)
    if embeddings_ok and pinecone_ok:
        print("🎉 All tests passed! Embeddings pipeline is ready.")
        print("\nTo run the full pipeline:")
        print("1. Ensure reddit_data.jsonl exists (run ingest-pipeline.py)")
        print("2. Set OPENAI_API_KEY and PINECONE_API_KEY in .env")
        print("3. Run: python scripts/embeddings-pipeline.py")
    else:
        print("❌ Some tests failed. Check the output above.")
        if not embeddings_ok:
            print("   - Fix OpenAI API key or embedding generation issues")
        if not pinecone_ok:
            print("   - Fix Pinecone API key or connection issues")

if __name__ == "__main__":
    main()
