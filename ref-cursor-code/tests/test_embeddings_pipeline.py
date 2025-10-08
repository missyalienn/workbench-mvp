#!/usr/bin/env python3
"""
Unit tests for embeddings_pipeline.py
Tests embedding generation, batch processing, and Pinecone operations.
"""

import os
import json
import pytest
import tempfile
import sys
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import List, Dict, Any

# Mock external dependencies before imports
sys.modules['pinecone'] = MagicMock()
sys.modules['openai'] = MagicMock()

# Import the module under test
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from embeddings_pipeline import (
    create_retry_session,
    generate_embeddings,
    _process_batch,
    _generate_embedding_with_retry,
    upsert_to_pinecone,
    main
)


class TestCreateRetrySession:
    """Test cases for create_retry_session function."""
    
    def test_create_retry_session_default(self):
        """Test creating retry session with default parameters."""
        session = create_retry_session()
        
        # Assertions
        assert session is not None
        assert hasattr(session, 'mount')
        assert hasattr(session, 'get')
        assert hasattr(session, 'post')
    
    def test_create_retry_session_custom_params(self):
        """Test creating retry session with custom parameters."""
        session = create_retry_session(max_retries=5, backoff_factor=2)
        
        # Assertions
        assert session is not None
        assert hasattr(session, 'mount')
    
    @patch('embeddings_pipeline.requests.Session')
    @patch('embeddings_pipeline.Retry')
    @patch('embeddings_pipeline.HTTPAdapter')
    def test_create_retry_session_mocking(self, mock_adapter, mock_retry, mock_session):
        """Test retry session creation with mocked dependencies."""
        # Setup mocks
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_adapter_instance = Mock()
        mock_adapter.return_value = mock_adapter_instance
        
        # Test
        session = create_retry_session(max_retries=3, backoff_factor=1)
        
        # Assertions
        mock_retry.assert_called_once_with(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        mock_adapter.assert_called_once_with(max_retries=mock_retry.return_value)
        mock_session_instance.mount.assert_any_call("http://", mock_adapter_instance)
        mock_session_instance.mount.assert_any_call("https://", mock_adapter_instance)


class TestGenerateEmbeddings:
    """Test cases for generate_embeddings function."""
    
    @patch('embeddings_pipeline._process_batch')
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-key')
    @patch('embeddings_pipeline.time.sleep')
    def test_generate_embeddings_success(self, mock_sleep, mock_process_batch):
        """Test successful embedding generation from JSONL file."""
        # Setup test data
        test_data = [
            '{"id": "post_1", "text": "Test post 1", "type": "post"}',
            '{"id": "comment_1", "text": "Test comment 1", "type": "comment"}',
            '{"id": "post_2", "text": "Test post 2", "type": "post"}'
        ]
        
        # Setup mock return values - each batch call returns different results
        mock_process_batch.side_effect = [
            [('post_1', [0.1, 0.2, 0.3], {'text': 'Test post 1', 'type': 'post'}),
             ('comment_1', [0.4, 0.5, 0.6], {'text': 'Test comment 1', 'type': 'comment'})],
            [('post_2', [0.7, 0.8, 0.9], {'text': 'Test post 2', 'type': 'post'})]
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('\n'.join(test_data))
            temp_file = f.name
        
        try:
            # Test
            result = generate_embeddings(temp_file, batch_size=2)
            
            # Assertions
            assert len(result) == 3
            assert result[0][0] == 'post_1'
            assert result[1][0] == 'comment_1'
            assert result[2][0] == 'post_2'
            
            # Check that _process_batch was called twice (batch_size=2)
            assert mock_process_batch.call_count == 2
            mock_sleep.assert_called()  # Rate limiting sleep
            
        finally:
            os.unlink(temp_file)
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', None)
    def test_generate_embeddings_no_api_key(self):
        """Test embedding generation without API key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": "test", "text": "test"}')
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                generate_embeddings(temp_file)
        finally:
            os.unlink(temp_file)
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-key')
    def test_generate_embeddings_file_not_found(self):
        """Test embedding generation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            generate_embeddings('nonexistent.jsonl')
    
    @patch('embeddings_pipeline._process_batch')
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-key')
    def test_generate_embeddings_malformed_json(self, mock_process_batch):
        """Test embedding generation with malformed JSON lines."""
        # Setup test data with malformed JSON
        test_data = [
            '{"id": "post_1", "text": "Test post 1", "type": "post"}',
            '{"id": "post_2", "text": "Test post 2", "type": "post"',  # Missing closing brace
            '{"id": "post_3", "text": "Test post 3", "type": "post"}'
        ]
        
        mock_process_batch.side_effect = [
            [('post_1', [0.1, 0.2, 0.3], {'text': 'Test post 1', 'type': 'post'})],
            [('post_3', [0.7, 0.8, 0.9], {'text': 'Test post 3', 'type': 'post'})]
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('\n'.join(test_data))
            temp_file = f.name
        
        try:
            # Test
            result = generate_embeddings(temp_file, batch_size=1)
            
            # Assertions - should process valid records and skip malformed ones
            assert len(result) == 2
            assert result[0][0] == 'post_1'
            assert result[1][0] == 'post_3'
            
        finally:
            os.unlink(temp_file)
    
    @patch('embeddings_pipeline._process_batch')
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-key')
    def test_generate_embeddings_empty_file(self, mock_process_batch):
        """Test embedding generation with empty file."""
        # Create empty temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_file = f.name
        
        try:
            # Test
            result = generate_embeddings(temp_file)
            
            # Assertions
            assert result == []
            mock_process_batch.assert_not_called()
            
        finally:
            os.unlink(temp_file)


class TestProcessBatch:
    """Test cases for _process_batch function."""
    
    @patch('embeddings_pipeline._generate_embedding_with_retry')
    def test_process_batch_success(self, mock_generate_embedding):
        """Test successful batch processing."""
        # Setup test data
        batch = [
            {
                'id': 'post_1',
                'text': 'Test post content',
                'type': 'post',
                'score': 0.85,
                'url': 'https://reddit.com/r/test/post_1'
            },
            {
                'id': 'comment_1',
                'text': 'Test comment content',
                'type': 'comment',
                'score': 0.75,
                'link_id': 'post_1'
            }
        ]
        
        # Setup mock return values
        mock_generate_embedding.side_effect = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.6, 0.7, 0.8, 0.9, 1.0]
        ]
        
        # Test
        result = _process_batch(batch, 1)
        
        # Assertions
        assert len(result) == 2
        
        # Check first result (post)
        assert result[0][0] == 'post_1'
        assert result[0][1] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert result[0][2]['type'] == 'post'
        assert result[0][2]['score'] == 0.85
        assert result[0][2]['url'] == 'https://reddit.com/r/test/post_1'
        assert 'link_id' not in result[0][2]
        
        # Check second result (comment)
        assert result[1][0] == 'comment_1'
        assert result[1][1] == [0.6, 0.7, 0.8, 0.9, 1.0]
        assert result[1][2]['type'] == 'comment'
        assert result[1][2]['score'] == 0.75
        assert result[1][2]['link_id'] == 'post_1'
        assert 'url' not in result[1][2]
        
        # Check that embedding generation was called for each record
        assert mock_generate_embedding.call_count == 2
    
    @patch('embeddings_pipeline._generate_embedding_with_retry')
    def test_process_batch_empty_text(self, mock_generate_embedding):
        """Test batch processing with empty text."""
        # Setup test data with empty text
        batch = [
            {
                'id': 'post_1',
                'text': '',
                'type': 'post'
            },
            {
                'id': 'post_2',
                'text': 'Valid text',
                'type': 'post'
            }
        ]
        
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Test
        result = _process_batch(batch, 1)
        
        # Assertions - should skip empty text record
        assert len(result) == 1
        assert result[0][0] == 'post_2'
        assert mock_generate_embedding.call_count == 1
    
    @patch('embeddings_pipeline._generate_embedding_with_retry')
    def test_process_batch_embedding_error(self, mock_generate_embedding):
        """Test batch processing with embedding generation error."""
        # Setup test data
        batch = [
            {
                'id': 'post_1',
                'text': 'Test text',
                'type': 'post'
            }
        ]
        
        # Setup mock to raise exception
        mock_generate_embedding.side_effect = Exception("Embedding error")
        
        # Test
        result = _process_batch(batch, 1)
        
        # Assertions - should skip failed record
        assert len(result) == 0
        mock_generate_embedding.assert_called_once()
    
    @patch('embeddings_pipeline._generate_embedding_with_retry')
    def test_process_batch_text_truncation(self, mock_generate_embedding):
        """Test batch processing with text truncation for metadata."""
        # Setup test data with long text
        long_text = 'a' * 2000  # Longer than 1000 character limit
        batch = [
            {
                'id': 'post_1',
                'text': long_text,
                'type': 'post'
            }
        ]
        
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Test
        result = _process_batch(batch, 1)
        
        # Assertions
        assert len(result) == 1
        assert len(result[0][2]['text']) == 1000  # Should be truncated
        assert result[0][2]['text'] == 'a' * 1000


class TestGenerateEmbeddingWithRetry:
    """Test cases for _generate_embedding_with_retry function."""
    
    @patch('embeddings_pipeline.openai.embeddings.create')
    @patch('embeddings_pipeline.time.sleep')
    def test_generate_embedding_success(self, mock_sleep, mock_create):
        """Test successful embedding generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_create.return_value = mock_response
        
        # Test
        result = _generate_embedding_with_retry("test text")
        
        # Assertions
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_create.assert_called_once_with(
            model="text-embedding-3-small",
            input="test text"
        )
        mock_sleep.assert_not_called()
    
    @patch('embeddings_pipeline.openai.embeddings.create')
    @patch('embeddings_pipeline.time.sleep')
    def test_generate_embedding_rate_limit_retry(self, mock_sleep, mock_create):
        """Test embedding generation with rate limit retry."""
        # Setup mock to fail twice then succeed
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        
        # Create a proper exception class that inherits from Exception
        class MockRateLimitError(Exception):
            pass
        
        # Mock the RateLimitError on the openai module
        with patch('embeddings_pipeline.openai.RateLimitError', MockRateLimitError):
            mock_create.side_effect = [
                MockRateLimitError("Rate limit"),
                MockRateLimitError("Rate limit"),
                mock_response
            ]
            
            # Test
            result = _generate_embedding_with_retry("test text", max_retries=3)
            
            # Assertions
            assert result == [0.1, 0.2, 0.3]
            assert mock_create.call_count == 3
            assert mock_sleep.call_count == 2  # Should sleep twice before success
    
    @patch('embeddings_pipeline.openai.embeddings.create')
    @patch('embeddings_pipeline.time.sleep')
    def test_generate_embedding_general_error_retry(self, mock_sleep, mock_create):
        """Test embedding generation with general error retry."""
        # Setup mock to fail once then succeed
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        
        # Create a proper exception class that inherits from Exception
        class MockRateLimitError(Exception):
            pass
        
        # Mock the RateLimitError on the openai module
        with patch('embeddings_pipeline.openai.RateLimitError', MockRateLimitError):
            mock_create.side_effect = [
                Exception("Network error"),
                mock_response
            ]
            
            # Test
            result = _generate_embedding_with_retry("test text", max_retries=2)
            
            # Assertions
            assert result == [0.1, 0.2, 0.3]
            assert mock_create.call_count == 2
            assert mock_sleep.call_count == 1
    
    @patch('embeddings_pipeline.openai.embeddings.create')
    @patch('embeddings_pipeline.time.sleep')
    def test_generate_embedding_rate_limit_exhausted(self, mock_sleep, mock_create):
        """Test embedding generation with rate limit exhaustion."""
        # Create a proper exception class that inherits from Exception
        class MockRateLimitError(Exception):
            pass
        
        # Setup mock to always fail
        mock_create.side_effect = MockRateLimitError("Rate limit")
        
        # Mock the RateLimitError on the openai module
        with patch('embeddings_pipeline.openai.RateLimitError', MockRateLimitError):
            # Test
            with pytest.raises(MockRateLimitError):  # Should raise the rate limit error
                _generate_embedding_with_retry("test text", max_retries=2)
            
            # Assertions
            assert mock_create.call_count == 2
            assert mock_sleep.call_count == 1  # Should sleep once before final failure


class TestUpsertToPinecone:
    """Test cases for upsert_to_pinecone function."""
    
    @patch('embeddings_pipeline.pc')
    @patch('embeddings_pipeline.PINECONE_INDEX_NAME', 'test-index')
    @patch('embeddings_pipeline.PINECONE_ENVIRONMENT', 'us-east-1')
    @patch('embeddings_pipeline.time.sleep')
    def test_upsert_to_pinecone_success(self, mock_sleep, mock_pc):
        """Test successful upsert to Pinecone."""
        # Setup mock
        mock_index_list = Mock()
        mock_index_list.names.return_value = ['test-index', 'other-index']
        mock_pc.list_indexes.return_value = mock_index_list
        
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test data
        vectors_list = [
            ('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'}),
            ('comment_1', [0.4, 0.5, 0.6], {'text': 'Test comment', 'type': 'comment'})
        ]
        
        # Test
        result = upsert_to_pinecone(vectors_list)
        
        # Assertions
        assert result is True
        mock_pc.list_indexes.assert_called_once()
        mock_pc.Index.assert_called_once_with('test-index')
        mock_index.upsert.assert_called_once()
        
        # Check upsert call arguments
        upsert_call = mock_index.upsert.call_args
        vectors = upsert_call[1]['vectors']
        assert len(vectors) == 2
        assert vectors[0]['id'] == 'post_1'
        assert vectors[0]['values'] == [0.1, 0.2, 0.3]
        assert vectors[0]['metadata'] == {'text': 'Test post', 'type': 'post'}
    
    @patch('embeddings_pipeline.pc')
    @patch('embeddings_pipeline.PINECONE_INDEX_NAME', 'missing-index')
    @patch('embeddings_pipeline.PINECONE_ENVIRONMENT', 'us-east-1')
    @patch('embeddings_pipeline.time.sleep')
    def test_upsert_to_pinecone_create_index(self, mock_sleep, mock_pc):
        """Test upsert to Pinecone with index creation."""
        # Setup mock - index doesn't exist initially
        mock_index_list = Mock()
        mock_index_list.names.return_value = ['other-index']
        mock_pc.list_indexes.return_value = mock_index_list
        
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test data
        vectors_list = [('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'})]
        
        # Test
        result = upsert_to_pinecone(vectors_list)
        
        # Assertions
        assert result is True
        mock_pc.create_index.assert_called_once()
        # Check that sleep was called with 10 (for index creation) and 0.1 (for batch delay)
        assert mock_sleep.call_count >= 1
        mock_index.upsert.assert_called_once()
    
    @patch('embeddings_pipeline.pc', None)
    def test_upsert_to_pinecone_no_client(self):
        """Test upsert to Pinecone when client is not initialized."""
        vectors_list = [('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'})]
        
        # Test
        with pytest.raises(ValueError, match="Pinecone client not initialized"):
            upsert_to_pinecone(vectors_list)
    
    @patch('embeddings_pipeline.pc')
    @patch('embeddings_pipeline.PINECONE_INDEX_NAME', 'test-index')
    @patch('embeddings_pipeline.time.sleep')
    def test_upsert_to_pinecone_large_batch(self, mock_sleep, mock_pc):
        """Test upsert to Pinecone with large batch (multiple upsert calls)."""
        # Setup mock
        mock_index_list = Mock()
        mock_index_list.names.return_value = ['test-index']
        mock_pc.list_indexes.return_value = mock_index_list
        
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Create large batch (150 items to trigger multiple upsert calls)
        vectors_list = []
        for i in range(150):
            vectors_list.append((f'id_{i}', [0.1, 0.2, 0.3], {'text': f'Test {i}'}))
        
        # Test
        result = upsert_to_pinecone(vectors_list)
        
        # Assertions
        assert result is True
        # Should be called twice (100 + 50 items)
        assert mock_index.upsert.call_count == 2
        # Should sleep between batches
        assert mock_sleep.call_count >= 1
    
    @patch('embeddings_pipeline.pc')
    @patch('embeddings_pipeline.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_to_pinecone_api_error(self, mock_pc):
        """Test upsert to Pinecone with API error."""
        # Setup mock to raise exception
        mock_index_list = Mock()
        mock_index_list.names.return_value = ['test-index']
        mock_pc.list_indexes.return_value = mock_index_list
        
        mock_index = Mock()
        mock_index.upsert.side_effect = Exception("API Error")
        mock_pc.Index.return_value = mock_index
        
        # Test data
        vectors_list = [('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'})]
        
        # Test
        result = upsert_to_pinecone(vectors_list)
        
        # Assertions
        assert result is False
        mock_index.upsert.assert_called_once()


class TestMainFunction:
    """Test cases for main function."""
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-openai-key')
    @patch('embeddings_pipeline.PINECONE_API_KEY', 'test-pinecone-key')
    @patch('embeddings_pipeline.generate_embeddings')
    @patch('embeddings_pipeline.upsert_to_pinecone')
    @patch('embeddings_pipeline.os.path.exists')
    def test_main_success(self, mock_exists, mock_upsert, mock_generate):
        """Test successful main function execution."""
        # Setup mocks
        mock_exists.return_value = True
        mock_generate.return_value = [
            ('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'})
        ]
        mock_upsert.return_value = True
        
        # Test
        main()
        
        # Assertions
        mock_exists.assert_called_once_with('reddit_data.jsonl')
        mock_generate.assert_called_once_with('reddit_data.jsonl')
        mock_upsert.assert_called_once()
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', None)
    def test_main_no_openai_key(self):
        """Test main function without OpenAI API key."""
        # Test
        main()
        
        # Should exit early without processing
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-openai-key')
    @patch('embeddings_pipeline.PINECONE_API_KEY', None)
    def test_main_no_pinecone_key(self):
        """Test main function without Pinecone API key."""
        # Test
        main()
        
        # Should exit early without processing
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-openai-key')
    @patch('embeddings_pipeline.PINECONE_API_KEY', 'test-pinecone-key')
    @patch('embeddings_pipeline.os.path.exists')
    def test_main_no_jsonl_file(self, mock_exists):
        """Test main function without JSONL file."""
        # Setup mock
        mock_exists.return_value = False
        
        # Test
        main()
        
        # Should exit early without processing
        mock_exists.assert_called_once_with('reddit_data.jsonl')
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-openai-key')
    @patch('embeddings_pipeline.PINECONE_API_KEY', 'test-pinecone-key')
    @patch('embeddings_pipeline.generate_embeddings')
    @patch('embeddings_pipeline.upsert_to_pinecone')
    @patch('embeddings_pipeline.os.path.exists')
    def test_main_no_vectors_generated(self, mock_exists, mock_upsert, mock_generate):
        """Test main function with no vectors generated."""
        # Setup mocks
        mock_exists.return_value = True
        mock_generate.return_value = []
        
        # Test
        main()
        
        # Assertions
        mock_generate.assert_called_once()
        mock_upsert.assert_not_called()
    
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-openai-key')
    @patch('embeddings_pipeline.PINECONE_API_KEY', 'test-pinecone-key')
    @patch('embeddings_pipeline.generate_embeddings')
    @patch('embeddings_pipeline.upsert_to_pinecone')
    @patch('embeddings_pipeline.os.path.exists')
    def test_main_upsert_failure(self, mock_exists, mock_upsert, mock_generate):
        """Test main function with upsert failure."""
        # Setup mocks
        mock_exists.return_value = True
        mock_generate.return_value = [
            ('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'})
        ]
        mock_upsert.return_value = False
        
        # Test
        main()
        
        # Assertions
        mock_generate.assert_called_once()
        mock_upsert.assert_called_once()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch('embeddings_pipeline._process_batch')
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-key')
    def test_generate_embeddings_single_record(self, mock_process_batch):
        """Test embedding generation with single record."""
        # Setup test data
        test_data = ['{"id": "post_1", "text": "Test post", "type": "post"}']
        
        mock_process_batch.return_value = [
            ('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'})
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('\n'.join(test_data))
            temp_file = f.name
        
        try:
            # Test
            result = generate_embeddings(temp_file, batch_size=100)
            
            # Assertions
            assert len(result) == 1
            assert result[0][0] == 'post_1'
            
        finally:
            os.unlink(temp_file)
    
    @patch('embeddings_pipeline._process_batch')
    @patch('embeddings_pipeline.OPENAI_API_KEY', 'test-key')
    def test_generate_embeddings_whitespace_lines(self, mock_process_batch):
        """Test embedding generation with whitespace-only lines."""
        # Setup test data with whitespace lines
        test_data = [
            '{"id": "post_1", "text": "Test post", "type": "post"}',
            '   ',  # Whitespace line
            '',     # Empty line
            '{"id": "post_2", "text": "Test post 2", "type": "post"}'
        ]
        
        mock_process_batch.side_effect = [
            [('post_1', [0.1, 0.2, 0.3], {'text': 'Test post', 'type': 'post'})],
            [('post_2', [0.4, 0.5, 0.6], {'text': 'Test post 2', 'type': 'post'})]
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('\n'.join(test_data))
            temp_file = f.name
        
        try:
            # Test
            result = generate_embeddings(temp_file, batch_size=1)
            
            # Assertions - should skip whitespace lines
            assert len(result) == 2
            assert result[0][0] == 'post_1'
            assert result[1][0] == 'post_2'
            
        finally:
            os.unlink(temp_file)
    
    @patch('embeddings_pipeline._generate_embedding_with_retry')
    def test_process_batch_missing_fields(self, mock_generate_embedding):
        """Test batch processing with missing fields."""
        # Setup test data with missing fields
        batch = [
            {
                'id': 'post_1',
                'text': 'Test post',
                # Missing 'type' field
            },
            {
                'id': 'post_2',
                'text': 'Test post 2',
                'type': 'post',
                # Missing 'score' field
            }
        ]
        
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Test
        result = _process_batch(batch, 1)
        
        # Assertions
        assert len(result) == 2
        
        # Check that missing fields get default values
        assert result[0][2]['type'] == ''  # Default empty string
        assert result[0][2]['score'] == 0  # Default 0
        assert result[1][2]['type'] == 'post'
        assert result[1][2]['score'] == 0  # Default 0
    
    @patch('embeddings_pipeline.pc')
    @patch('embeddings_pipeline.PINECONE_INDEX_NAME', 'test-index')
    def test_upsert_to_pinecone_empty_vectors(self, mock_pc):
        """Test upsert to Pinecone with empty vectors list."""
        # Setup mock
        mock_index_list = Mock()
        mock_index_list.names.return_value = ['test-index']
        mock_pc.list_indexes.return_value = mock_index_list
        
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        
        # Test
        result = upsert_to_pinecone([])
        
        # Assertions
        assert result is True
        mock_pc.Index.assert_called_once()
        # Empty list should not call upsert
        mock_index.upsert.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
