#!/usr/bin/env python3
"""
Unit tests for vector_store.py
Tests Pinecone operations, semantic search, and vector upserting.
"""

import os
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Mock Pinecone module before any imports
sys.modules['pinecone'] = MagicMock()

# Import the module under test
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from vector_store import (
    init_pinecone,
    semantic_search,
    upsert_embeddings
)


class TestInitPinecone:
    """Test cases for init_pinecone function."""
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_init_pinecone_success(self, mock_pc):
        """Test successful Pinecone initialization."""
        # Setup mock
        mock_index_list = Mock()
        mock_index_list.names.return_value = ['test-index', 'other-index']
        mock_pc.list_indexes.return_value = mock_index_list
        
        # Test
        result = init_pinecone()
        
        # Assertions
        assert result is True
        mock_pc.list_indexes.assert_called_once()
        mock_index_list.names.assert_called_once()
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'missing-index')
    def test_init_pinecone_index_not_found(self, mock_pc):
        """Test Pinecone initialization when index doesn't exist."""
        # Setup mock
        mock_index_list = Mock()
        mock_index_list.names.return_value = ['other-index', 'another-index']
        mock_pc.list_indexes.return_value = mock_index_list
        
        # Test
        result = init_pinecone()
        
        # Assertions
        assert result is False
        mock_pc.list_indexes.assert_called_once()
        mock_index_list.names.assert_called_once()
    
    @patch('vector_store.pc', None)
    def test_init_pinecone_no_client(self):
        """Test Pinecone initialization when client is None."""
        # Test
        result = init_pinecone()
        
        # Assertions
        assert result is False
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_init_pinecone_api_error(self, mock_pc):
        """Test Pinecone initialization with API error."""
        # Setup mock to raise exception
        mock_pc.list_indexes.side_effect = Exception("API Error")
        
        # Test
        result = init_pinecone()
        
        # Assertions
        assert result is False
        mock_pc.list_indexes.assert_called_once()


class TestSemanticSearch:
    """Test cases for semantic_search function."""
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_semantic_search_success(self, mock_pc):
        """Test successful semantic search."""
        # Setup mock response
        mock_match1 = Mock()
        mock_match1.id = 'post_123'
        mock_match1.score = 0.95
        mock_match1.metadata = {
            'text': 'Test post content',
            'type': 'post',
            'source': 'reddit',
            'score': 0.85,
            'created_at': 1234567890,
            'url': 'https://reddit.com/r/test/post_123'
        }
        
        mock_match2 = Mock()
        mock_match2.id = 'comment_456'
        mock_match2.score = 0.88
        mock_match2.metadata = {
            'text': 'Test comment content',
            'type': 'comment',
            'source': 'reddit',
            'score': 0.75,
            'created_at': 1234567891,
            'link_id': 'post_123'
        }
        
        mock_search_result = Mock()
        mock_search_result.matches = [mock_match1, mock_match2]
        
        mock_index = Mock()
        mock_index.query.return_value = mock_search_result
        mock_pc.Index.return_value = mock_index
        
        # Test
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = semantic_search(query_embedding, top_k=5)
        
        # Assertions
        assert len(result) == 2
        
        # Check first result (post)
        assert result[0]['id'] == 'post_123'
        assert result[0]['score'] == 0.95
        assert result[0]['text'] == 'Test post content'
        assert result[0]['type'] == 'post'
        assert result[0]['source'] == 'reddit'
        assert result[0]['score_original'] == 0.85
        assert result[0]['created_at'] == 1234567890
        assert result[0]['url'] == 'https://reddit.com/r/test/post_123'
        assert 'link_id' not in result[0]
        
        # Check second result (comment)
        assert result[1]['id'] == 'comment_456'
        assert result[1]['score'] == 0.88
        assert result[1]['text'] == 'Test comment content'
        assert result[1]['type'] == 'comment'
        assert result[1]['source'] == 'reddit'
        assert result[1]['score_original'] == 0.75
        assert result[1]['created_at'] == 1234567891
        assert result[1]['link_id'] == 'post_123'
        assert 'url' not in result[1]
        
        # Check API call
        mock_pc.Index.assert_called_once_with('test-index')
        mock_index.query.assert_called_once_with(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_semantic_search_custom_top_k(self, mock_pc):
        """Test semantic search with custom top_k parameter."""
        # Setup mock response
        mock_search_result = Mock()
        mock_search_result.matches = []
        mock_index = Mock()
        mock_index.query.return_value = mock_search_result
        mock_pc.Index.return_value = mock_index
        
        # Test
        query_embedding = [0.1, 0.2, 0.3]
        result = semantic_search(query_embedding, top_k=10)
        
        # Assertions
        assert result == []
        mock_index.query.assert_called_once_with(
            vector=query_embedding,
            top_k=10,
            include_metadata=True
        )
    
    @patch('vector_store.pc', None)
    def test_semantic_search_no_client(self):
        """Test semantic search when Pinecone client is not initialized."""
        query_embedding = [0.1, 0.2, 0.3]
        
        # Test
        with pytest.raises(ValueError, match="Pinecone client not initialized"):
            semantic_search(query_embedding)
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_semantic_search_api_error(self, mock_pc):
        """Test semantic search with API error."""
        # Setup mock to raise exception
        mock_index = Mock()
        mock_index.query.side_effect = Exception("API Error")
        mock_pc.Index.return_value = mock_index
        
        # Test
        query_embedding = [0.1, 0.2, 0.3]
        with pytest.raises(Exception, match="API Error"):
            semantic_search(query_embedding)
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_semantic_search_missing_metadata(self, mock_pc):
        """Test semantic search with missing metadata fields."""
        # Setup mock response with minimal metadata
        mock_match = Mock()
        mock_match.id = 'post_123'
        mock_match.score = 0.95
        mock_match.metadata = {}  # Empty metadata
        
        mock_search_result = Mock()
        mock_search_result.matches = [mock_match]
        
        mock_index = Mock()
        mock_index.query.return_value = mock_search_result
        mock_pc.Index.return_value = mock_index
        
        # Test
        query_embedding = [0.1, 0.2, 0.3]
        result = semantic_search(query_embedding)
        
        # Assertions
        assert len(result) == 1
        assert result[0]['id'] == 'post_123'
        assert result[0]['score'] == 0.95
        assert result[0]['text'] == ''
        assert result[0]['type'] == ''
        assert result[0]['source'] == 'reddit'  # Default value
        assert result[0]['score_original'] == 0
        assert result[0]['created_at'] == 0
        assert 'url' not in result[0]
        assert 'link_id' not in result[0]


class TestUpsertEmbeddings:
    """Test cases for upsert_embeddings function."""
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_embeddings_success(self, mock_pc):
        """Test successful embedding upsert."""
        # Setup mock
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test data
        embeddings = [
            ('post_123', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'}),
            ('comment_456', [0.4, 0.5, 0.6], {'text': 'Test comment', 'type': 'comment'})
        ]
        
        # Test
        result = upsert_embeddings(embeddings)
        
        # Assertions
        assert result is True
        mock_pc.Index.assert_called_once_with('test-index')
        mock_index.upsert.assert_called_once()
        
        # Check upsert call arguments
        upsert_call = mock_index.upsert.call_args
        vectors = upsert_call[1]['vectors']
        assert len(vectors) == 2
        assert vectors[0]['id'] == 'post_123'
        assert vectors[0]['values'] == [0.1, 0.2, 0.3]
        assert vectors[0]['metadata'] == {'text': 'Test post', 'type': 'post'}
        assert vectors[1]['id'] == 'comment_456'
        assert vectors[1]['values'] == [0.4, 0.5, 0.6]
        assert vectors[1]['metadata'] == {'text': 'Test comment', 'type': 'comment'}
    
    @patch('vector_store.pc')
    def test_upsert_embeddings_custom_index(self, mock_pc):
        """Test embedding upsert with custom index name."""
        # Setup mock
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test data
        embeddings = [('test_id', [0.1, 0.2, 0.3], {'text': 'Test'})]
        
        # Test
        result = upsert_embeddings(embeddings, index_name='custom-index')
        
        # Assertions
        assert result is True
        mock_pc.Index.assert_called_once_with('custom-index')
        mock_index.upsert.assert_called_once()
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_embeddings_large_batch(self, mock_pc):
        """Test embedding upsert with large batch (multiple upsert calls)."""
        # Setup mock
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Create large batch (150 items to trigger multiple upsert calls)
        embeddings = []
        for i in range(150):
            embeddings.append((f'id_{i}', [0.1, 0.2, 0.3], {'text': f'Test {i}'}))
        
        # Test
        result = upsert_embeddings(embeddings)
        
        # Assertions
        assert result is True
        # Should be called twice (100 + 50 items)
        assert mock_index.upsert.call_count == 2
        
        # Check first batch
        first_call = mock_index.upsert.call_args_list[0]
        first_vectors = first_call[1]['vectors']
        assert len(first_vectors) == 100
        assert first_vectors[0]['id'] == 'id_0'
        assert first_vectors[99]['id'] == 'id_99'
        
        # Check second batch
        second_call = mock_index.upsert.call_args_list[1]
        second_vectors = second_call[1]['vectors']
        assert len(second_vectors) == 50
        assert second_vectors[0]['id'] == 'id_100'
        assert second_vectors[49]['id'] == 'id_149'
    
    @patch('vector_store.pc', None)
    def test_upsert_embeddings_no_client(self):
        """Test embedding upsert when Pinecone client is not initialized."""
        embeddings = [('test_id', [0.1, 0.2, 0.3], {'text': 'Test'})]
        
        # Test
        with pytest.raises(ValueError, match="Pinecone client not initialized"):
            upsert_embeddings(embeddings)
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_embeddings_api_error(self, mock_pc):
        """Test embedding upsert with API error."""
        # Setup mock to raise exception
        mock_index = Mock()
        mock_index.upsert.side_effect = Exception("API Error")
        mock_pc.Index.return_value = mock_index
        
        # Test data
        embeddings = [('test_id', [0.1, 0.2, 0.3], {'text': 'Test'})]
        
        # Test
        result = upsert_embeddings(embeddings)
        
        # Assertions
        assert result is False
        mock_pc.Index.assert_called_once()
        mock_index.upsert.assert_called_once()
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_embeddings_empty_list(self, mock_pc):
        """Test embedding upsert with empty embeddings list."""
        # Setup mock
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test
        result = upsert_embeddings([])
        
        # Assertions
        assert result is True
        mock_pc.Index.assert_called_once()
        # Empty list should not call upsert
        mock_index.upsert.assert_not_called()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_semantic_search_empty_embedding(self, mock_pc):
        """Test semantic search with empty embedding vector."""
        # Setup mock response
        mock_search_result = Mock()
        mock_search_result.matches = []
        mock_index = Mock()
        mock_index.query.return_value = mock_search_result
        mock_pc.Index.return_value = mock_index
        
        # Test
        result = semantic_search([])
        
        # Assertions
        assert result == []
        mock_index.query.assert_called_once_with(
            vector=[],
            top_k=5,
            include_metadata=True
        )
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_semantic_search_zero_top_k(self, mock_pc):
        """Test semantic search with top_k=0."""
        # Setup mock response
        mock_search_result = Mock()
        mock_search_result.matches = []
        mock_index = Mock()
        mock_index.query.return_value = mock_search_result
        mock_pc.Index.return_value = mock_index
        
        # Test
        result = semantic_search([0.1, 0.2, 0.3], top_k=0)
        
        # Assertions
        assert result == []
        mock_index.query.assert_called_once_with(
            vector=[0.1, 0.2, 0.3],
            top_k=0,
            include_metadata=True
        )
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_embeddings_malformed_data(self, mock_pc):
        """Test embedding upsert with malformed data."""
        # Setup mock
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test data with malformed tuple (missing metadata)
        embeddings = [('test_id', [0.1, 0.2, 0.3])]  # Missing metadata
        
        # Test - should return False due to error
        result = upsert_embeddings(embeddings)
        
        # Assertions
        assert result is False
        mock_pc.Index.assert_called_once()
        mock_index.upsert.assert_not_called()
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_semantic_search_very_large_embedding(self, mock_pc):
        """Test semantic search with very large embedding vector."""
        # Setup mock response
        mock_search_result = Mock()
        mock_search_result.matches = []
        mock_index = Mock()
        mock_index.query.return_value = mock_search_result
        mock_pc.Index.return_value = mock_index
        
        # Test with large embedding (1536 dimensions - typical for OpenAI)
        large_embedding = [0.1] * 1536
        
        # Test
        result = semantic_search(large_embedding)
        
        # Assertions
        assert result == []
        mock_index.query.assert_called_once_with(
            vector=large_embedding,
            top_k=5,
            include_metadata=True
        )
    
    @patch('vector_store.pc')
    @patch('vector_store.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_embeddings_special_characters_in_id(self, mock_pc):
        """Test embedding upsert with special characters in ID."""
        # Setup mock
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test data with special characters
        embeddings = [
            ('post_123!@#', [0.1, 0.2, 0.3], {'text': 'Test with special chars'}),
            ('comment-456_$%', [0.4, 0.5, 0.6], {'text': 'Another test'})
        ]
        
        # Test
        result = upsert_embeddings(embeddings)
        
        # Assertions
        assert result is True
        mock_index.upsert.assert_called_once()
        
        # Check that special characters are preserved
        upsert_call = mock_index.upsert.call_args
        vectors = upsert_call[1]['vectors']
        assert vectors[0]['id'] == 'post_123!@#'
        assert vectors[1]['id'] == 'comment-456_$%'


if __name__ == "__main__":
    pytest.main([__file__])