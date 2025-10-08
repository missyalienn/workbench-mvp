#!/usr/bin/env python3
"""
Unit tests for llm_client.py
Tests OpenAI API interactions, retry logic, and utility functions.
"""

import os
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the module under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from llm_client import (
    generate_embedding,
    generate_chat_completion,
    format_context_for_llm,
    create_rag_messages
)


class TestGenerateEmbedding:
    """Test cases for generate_embedding function."""
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_embedding_success(self, mock_openai):
        """Test successful embedding generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_openai.embeddings.create.return_value = mock_response
        
        # Test
        result = generate_embedding("test text")
        
        # Assertions
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_openai.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input="test text"
        )
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_embedding_custom_model(self, mock_openai):
        """Test embedding generation with custom model."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_openai.embeddings.create.return_value = mock_response
        
        # Test
        result = generate_embedding("test text", model="text-embedding-3-large")
        
        # Assertions
        assert result == [0.1, 0.2, 0.3]
        mock_openai.embeddings.create.assert_called_once_with(
            model="text-embedding-3-large",
            input="test text"
        )
    
    @patch('llm_client.OPENAI_API_KEY', None)
    def test_generate_embedding_no_api_key(self):
        """Test embedding generation without API key."""
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            generate_embedding("test text")
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    @patch('llm_client.time.sleep')
    def test_generate_embedding_rate_limit_retry_success(self, mock_sleep, mock_openai):
        """Test retry logic for rate limit errors."""
        # Setup mock to fail twice then succeed
        from openai import RateLimitError
        
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        
        # Create mock response object for RateLimitError
        mock_response_obj = Mock()
        mock_response_obj.request = Mock()
        
        # Mock the RateLimitError on the openai module
        mock_openai.RateLimitError = RateLimitError
        
        mock_openai.embeddings.create.side_effect = [
            RateLimitError("Rate limit", response=mock_response_obj, body=None),
            RateLimitError("Rate limit", response=mock_response_obj, body=None),
            mock_response
        ]
        
        # Test
        result = generate_embedding("test text", max_retries=3)
        
        # Assertions
        assert result == [0.1, 0.2, 0.3]
        assert mock_openai.embeddings.create.call_count == 3
        assert mock_sleep.call_count == 2  # Should sleep twice before success
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    @patch('llm_client.time.sleep')
    def test_generate_embedding_rate_limit_exhausted(self, mock_sleep, mock_openai):
        """Test rate limit retry exhaustion."""
        from openai import RateLimitError
        
        # Create mock response object for RateLimitError
        mock_response_obj = Mock()
        mock_response_obj.request = Mock()
        
        # Mock the RateLimitError on the openai module
        mock_openai.RateLimitError = RateLimitError
        
        mock_openai.embeddings.create.side_effect = RateLimitError("Rate limit", response=mock_response_obj, body=None)
        
        # Test
        with pytest.raises(RateLimitError):
            generate_embedding("test text", max_retries=2)
        
        # Assertions
        assert mock_openai.embeddings.create.call_count == 2
        assert mock_sleep.call_count == 1  # Should sleep once before final failure
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    @patch('llm_client.time.sleep')
    def test_generate_embedding_general_exception_retry(self, mock_sleep, mock_openai):
        """Test retry logic for general exceptions."""
        from openai import RateLimitError
        
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        
        # Mock the RateLimitError on the openai module
        mock_openai.RateLimitError = RateLimitError
        
        mock_openai.embeddings.create.side_effect = [
            Exception("Network error"),
            mock_response
        ]
        
        # Test
        result = generate_embedding("test text", max_retries=2)
        
        # Assertions
        assert result == [0.1, 0.2, 0.3]
        assert mock_openai.embeddings.create.call_count == 2
        assert mock_sleep.call_count == 1


class TestGenerateChatCompletion:
    """Test cases for generate_chat_completion function."""
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_chat_completion_success(self, mock_openai):
        """Test successful chat completion generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_openai.chat.completions.create.return_value = mock_response
        
        # Test
        messages = [{"role": "user", "content": "Hello"}]
        result = generate_chat_completion(messages)
        
        # Assertions
        assert result == "Test response"
        mock_openai.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_chat_completion_custom_params(self, mock_openai):
        """Test chat completion with custom parameters."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Custom response"
        mock_openai.chat.completions.create.return_value = mock_response
        
        # Test
        messages = [{"role": "user", "content": "Hello"}]
        result = generate_chat_completion(
            messages, 
            model="gpt-4", 
            max_tokens=500, 
            temperature=0.5
        )
        
        # Assertions
        assert result == "Custom response"
        mock_openai.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.5
        )
    
    @patch('llm_client.OPENAI_API_KEY', None)
    def test_generate_chat_completion_no_api_key(self):
        """Test chat completion without API key."""
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            generate_chat_completion(messages)
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_chat_completion_rate_limit_error(self, mock_openai):
        """Test rate limit error handling."""
        from openai import RateLimitError
        
        # Create mock response object for RateLimitError
        mock_response_obj = Mock()
        mock_response_obj.request = Mock()
        
        # Mock the RateLimitError on the openai module
        mock_openai.RateLimitError = RateLimitError
        
        mock_openai.chat.completions.create.side_effect = RateLimitError("Rate limit", response=mock_response_obj, body=None)
        
        # Test
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(RateLimitError):
            generate_chat_completion(messages)
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_chat_completion_general_error(self, mock_openai):
        """Test general error handling."""
        from openai import RateLimitError
        
        # Mock the RateLimitError on the openai module
        mock_openai.RateLimitError = RateLimitError
        
        mock_openai.chat.completions.create.side_effect = Exception("Network error")
        
        # Test
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(Exception, match="Network error"):
            generate_chat_completion(messages)


class TestFormatContextForLLM:
    """Test cases for format_context_for_llm function."""
    
    def test_format_context_empty_results(self):
        """Test formatting with empty search results."""
        result = format_context_for_llm([])
        assert result == "No relevant context found."
    
    def test_format_context_single_result(self):
        """Test formatting with single search result."""
        search_results = [{
            'id': 'post_123',
            'type': 'comment',
            'text': 'This is a test comment',
            'score': 0.85
        }]
        
        result = format_context_for_llm(search_results)
        
        expected = """[Source 1: post_123]
Type: comment
Text: This is a test comment
Relevance Score: 0.850
"""
        
        assert result == expected
    
    def test_format_context_multiple_results(self):
        """Test formatting with multiple search results."""
        search_results = [
            {
                'id': 'post_123',
                'type': 'comment',
                'text': 'First comment',
                'score': 0.85
            },
            {
                'id': 'post_456',
                'type': 'post',
                'text': 'Second post',
                'score': 0.92,
                'url': 'https://reddit.com/r/test/post_456'
            }
        ]
        
        result = format_context_for_llm(search_results)
        
        expected = """[Source 1: post_123]
Type: comment
Text: First comment
Relevance Score: 0.850

---
[Source 2: post_456]
Type: post
Text: Second post
Relevance Score: 0.920
URL: https://reddit.com/r/test/post_456
"""
        
        assert result == expected
    
    def test_format_context_with_url(self):
        """Test formatting with URL in search result."""
        search_results = [{
            'id': 'post_789',
            'type': 'post',
            'text': 'Test post with URL',
            'score': 0.75,
            'url': 'https://reddit.com/r/diy/comments/abc123'
        }]
        
        result = format_context_for_llm(search_results)
        
        assert 'URL: https://reddit.com/r/diy/comments/abc123' in result
    
    def test_format_context_without_url(self):
        """Test formatting without URL in search result."""
        search_results = [{
            'id': 'post_789',
            'type': 'post',
            'text': 'Test post without URL',
            'score': 0.75
        }]
        
        result = format_context_for_llm(search_results)
        
        assert 'URL:' not in result


class TestCreateRagMessages:
    """Test cases for create_rag_messages function."""
    
    def test_create_rag_messages_basic(self):
        """Test basic RAG message creation."""
        user_question = "How do I fix a leaky faucet?"
        context = "[Source 1: post_123]\nType: comment\nText: Use plumber's tape\nRelevance Score: 0.850"
        
        result = create_rag_messages(user_question, context)
        
        # Check structure
        assert len(result) == 2
        assert result[0]['role'] == 'system'
        assert result[1]['role'] == 'user'
        
        # Check system prompt
        assert "DIY questions" in result[0]['content']
        assert "Reddit discussions" in result[0]['content']
        assert "cite your sources" in result[0]['content']
        
        # Check user message
        assert user_question in result[1]['content']
        assert context in result[1]['content']
        assert "[source: post_id]" in result[1]['content']
    
    def test_create_rag_messages_empty_context(self):
        """Test RAG message creation with empty context."""
        user_question = "How do I fix a leaky faucet?"
        context = "No relevant context found."
        
        result = create_rag_messages(user_question, context)
        
        assert len(result) == 2
        assert context in result[1]['content']
        assert user_question in result[1]['content']
    
    def test_create_rag_messages_complex_question(self):
        """Test RAG message creation with complex question."""
        user_question = "What are the best practices for electrical work in a bathroom renovation?"
        context = """[Source 1: post_456]
Type: post
Text: Always use GFCI outlets in bathrooms
Relevance Score: 0.920
---
[Source 2: post_789]
Type: comment
Text: Check local building codes first
Relevance Score: 0.850"""
        
        result = create_rag_messages(user_question, context)
        
        assert user_question in result[1]['content']
        assert "GFCI outlets" in result[1]['content']
        assert "building codes" in result[1]['content']
    
    def test_create_rag_messages_system_prompt_content(self):
        """Test that system prompt contains expected content."""
        user_question = "Test question"
        context = "Test context"
        
        result = create_rag_messages(user_question, context)
        system_prompt = result[0]['content']
        
        # Check key elements of system prompt
        assert "assistant" in system_prompt.lower()
        assert "DIY questions" in system_prompt
        assert "Reddit discussions" in system_prompt
        assert "context" in system_prompt.lower()
        assert "cite" in system_prompt.lower()
        assert "sources" in system_prompt.lower()
        assert "concise" in system_prompt.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_embedding_empty_text(self, mock_openai):
        """Test embedding generation with empty text."""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = []
        mock_openai.embeddings.create.return_value = mock_response
        
        result = generate_embedding("")
        assert result == []
    
    @patch('llm_client.openai')
    @patch('llm_client.OPENAI_API_KEY', 'test-key')
    def test_generate_embedding_very_long_text(self, mock_openai):
        """Test embedding generation with very long text."""
        long_text = "a" * 10000  # 10k characters
        
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536  # Typical embedding size
        mock_openai.embeddings.create.return_value = mock_response
        
        result = generate_embedding(long_text)
        assert len(result) == 1536
    
    def test_format_context_malformed_results(self):
        """Test formatting with malformed search results."""
        # Missing required fields
        search_results = [{'id': 'post_123'}]  # Missing type, text, score
        
        # Should raise KeyError for missing fields
        with pytest.raises(KeyError):
            format_context_for_llm(search_results)
    
    def test_create_rag_messages_special_characters(self):
        """Test RAG message creation with special characters."""
        user_question = "How do I fix a faucet with \"special\" characters & symbols?"
        context = "Test context with <html> tags and & symbols"
        
        result = create_rag_messages(user_question, context)
        
        assert user_question in result[1]['content']
        assert context in result[1]['content']
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__])
