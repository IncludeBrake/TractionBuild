#!/usr/bin/env python3
"""
Test suite for tractionbuild custom tools.
Tests all the new tools for functionality and error handling.
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tractionbuild.tools.summarization_tool import SummarizationTool
from tractionbuild.tools.compliance_tool import ComplianceCheckerTool
from tractionbuild.tools.sustainability_tool import SustainabilityTrackerTool, track_emissions
from tractionbuild.tools.celery_execution_tool import CeleryExecutionTool
from tractionbuild.tools.x_semantic_search_tool import XSemanticSearchTool
from tractionbuild.tools.market_oracle_tool import MarketOracleTool

class TestSummarizationTool:
    """Test cases for the SummarizationTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SummarizationTool()
        self.test_text = "Artificial intelligence is transforming the way we work and live. From virtual assistants to autonomous vehicles, AI is becoming increasingly integrated into our daily lives."
    
    @patch('requests.post')
    def test_ollama_success(self, mock_post):
        """Test successful Ollama summarization."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "AI is revolutionizing work and daily life."}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.tool._run(self.test_text)
        
        assert "AI is revolutionizing" in result
        mock_post.assert_called_once()
    
    @patch('requests.post')
    @patch('openai.OpenAI')
    def test_openai_fallback(self, mock_openai, mock_post):
        """Test OpenAI fallback when Ollama fails."""
        # Mock Ollama failure
        mock_post.side_effect = Exception("Ollama failed")
        
        # Mock OpenAI success
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "AI is changing work and life."
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client
        
        result = self.tool._run(self.test_text)
        
        assert "AI is changing" in result
        mock_openai.assert_called_once()
    
    def test_invalid_input(self):
        """Test handling of invalid input."""
        result = self.tool._run("")
        assert "failed" in result.lower()

class TestComplianceTool:
    """Test cases for the ComplianceCheckerTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ComplianceCheckerTool()
        self.test_text = "Contact Jane Doe at jane.doe@example.com or call 555-123-4567"
    
    def test_pii_detection(self):
        """Test PII detection and anonymization."""
        result = self.tool._run(self.test_text)
        
        assert "anonymized_text" in result
        assert result["pii_detected"] is True
        assert result["gdpr_compliant"] is True
        assert "<EMAIL_ADDRESS>" in result["anonymized_text"] or "<PERSON>" in result["anonymized_text"]
    
    def test_scan_only(self):
        """Test scan-only functionality."""
        result = self.tool.scan_only(self.test_text)
        
        assert "pii_detected" in result
        assert result["pii_detected"] is True
        assert "entities" in result
        assert len(result["entities"]) > 0
    
    def test_no_pii(self):
        """Test text with no PII."""
        clean_text = "This is a sample text without any personal information."
        result = self.tool._run(clean_text)
        
        assert result["pii_detected"] is False
        assert result["gdpr_compliant"] is True

class TestSustainabilityTool:
    """Test cases for the SustainabilityTrackerTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SustainabilityTrackerTool()
    
    def test_emissions_tracking(self):
        """Test basic emissions tracking."""
        result = self.tool._run("test_function", "test_project")
        
        assert "co2_emissions_kg" in result
        assert "status" in result
        assert result["function_name"] == "test_function"
        assert result["project_name"] == "test_project"
    
    def test_decorator(self):
        """Test the emissions tracking decorator."""
        @track_emissions
        def sample_function():
            return "test result"
        
        result = sample_function()
        assert result == "test result"
    
    def test_emissions_summary(self):
        """Test emissions summary generation."""
        result = self.tool.get_emissions_summary("test_project")
        
        assert "total_emissions_kg" in result
        assert "total_runs" in result
        assert "average_emissions_per_run" in result

class TestCeleryExecutionTool:
    """Test cases for the CeleryExecutionTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379/0'}):
            self.tool = CeleryExecutionTool()
    
    @patch('celery.Celery.send_task')
    def test_task_execution(self, mock_send_task):
        """Test task execution."""
        mock_task = MagicMock()
        mock_task.id = "test_task_id"
        mock_send_task.return_value = mock_task
        
        result = self.tool._run("test_task", ["arg1"], {"kwarg1": "value1"}, "test_queue")
        
        assert result["task_id"] == "test_task_id"
        assert result["status"] == "PENDING"
        assert result["task_name"] == "test_task"
        mock_send_task.assert_called_once()
    
    @patch('celery.Celery.AsyncResult')
    def test_task_status(self, mock_async_result):
        """Test task status checking."""
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = "task completed"
        mock_async_result.return_value = mock_result
        
        result = self.tool.get_task_status("test_task_id")
        
        assert result["status"] == "SUCCESS"
        assert result["result"] == "task completed"

class TestXSemanticSearchTool:
    """Test cases for the XSemanticSearchTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = XSemanticSearchTool()
        self.test_query = "artificial intelligence"
    
    def test_mock_search_results(self):
        """Test mock search results when API is unavailable."""
        result = self.tool._run(self.test_query, 5, "en")
        
        assert "results" in result
        assert "total_results" in result
        assert result["source"] == "mock_data"
        assert len(result["results"]) <= 5
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis functionality."""
        mock_tweets = [
            {"text": "This is great! I love it."},
            {"text": "This is terrible and awful."},
            {"text": "This is a neutral statement."}
        ]
        
        result = self.tool.analyze_sentiment(mock_tweets)
        
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result
        assert "overall_sentiment" in result
    
    def test_trending_topics(self):
        """Test trending topics functionality."""
        result = self.tool.get_trending_topics("en")
        
        assert "trends" in result
        assert "total_trends" in result
        assert result["source"] == "mock_data"

class TestMarketOracleTool:
    """Test cases for the MarketOracleTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = MarketOracleTool()
        self.test_topic = "artificial intelligence"
    
    @pytest.mark.asyncio
    async def test_market_scanning(self):
        """Test market scanning functionality."""
        result = await self.tool._arun(self.test_topic)
        
        assert "seo_trends" in result
        assert "reddit_discussion" in result
        assert "market_insights" in result
        assert "keyword_volume" in result["seo_trends"]
        assert "sentiment" in result["reddit_discussion"]
        assert "opportunity_score" in result["market_insights"]

# Integration tests
class TestToolIntegration:
    """Integration tests for tool combinations."""
    
    def test_summarization_with_compliance(self):
        """Test summarization tool with compliance checking."""
        summarization_tool = SummarizationTool()
        compliance_tool = ComplianceCheckerTool()
        
        test_text = "Contact John Smith at john.smith@example.com about AI trends."
        
        # First summarize
        summary = summarization_tool._run(test_text)
        
        # Then check compliance
        compliance_result = compliance_tool._run(summary)
        
        assert compliance_result["gdpr_compliant"] is True
    
    def test_sustainability_with_celery(self):
        """Test sustainability tracking with Celery execution."""
        sustainability_tool = SustainabilityTrackerTool()
        celery_tool = CeleryExecutionTool()
        
        # Track emissions of a Celery task
        result = sustainability_tool._run("celery_task_execution", "tractionbuild_project")
        
        assert "co2_emissions_kg" in result
        assert result["status"] == "success"

# Performance tests
class TestToolPerformance:
    """Performance tests for tools."""
    
    def test_summarization_performance(self):
        """Test summarization tool performance."""
        tool = SummarizationTool()
        long_text = "This is a very long text. " * 100
        
        import time
        start_time = time.time()
        result = tool._run(long_text)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 60  # Should complete within 60 seconds
        assert len(result) > 0
    
    def test_compliance_performance(self):
        """Test compliance tool performance."""
        tool = ComplianceCheckerTool()
        large_text = "Contact person1@example.com, person2@example.com, person3@example.com. " * 50
        
        import time
        start_time = time.time()
        result = tool._run(large_text)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 30  # Should complete within 30 seconds
        assert result["gdpr_compliant"] is True

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
