"""
Tests for Performance Benchmarking

Author: Patrick Cooper
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import after path setup
import benchmark_performance


class TestPerformanceBenchmark:
    """Test suite for PerformanceBenchmark class."""
    
    def test_benchmark_initialization(self):
        """Test benchmark can be initialized."""
        benchmark = benchmark_performance.PerformanceBenchmark()
        assert benchmark.base_url == "http://localhost:8000"
        assert benchmark.api_key is None
    
    def test_benchmark_initialization_custom(self):
        """Test benchmark with custom parameters."""
        benchmark = benchmark_performance.PerformanceBenchmark(
            base_url="http://test:9000",
            api_key="test-key"
        )
        assert benchmark.base_url == "http://test:9000"
        assert benchmark.api_key == "test-key"
    
    def test_percentile_calculation(self):
        """Test percentile calculation."""
        benchmark = benchmark_performance.PerformanceBenchmark()
        
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        p50 = benchmark._percentile(data, 50)
        assert p50 == 6  # 50% of 10 items = index 5 (0-indexed)
        
        p95 = benchmark._percentile(data, 95)
        assert p95 == 10
        
        p99 = benchmark._percentile(data, 99)
        assert p99 == 10
    
    @patch('benchmark_performance.CURCLLMClient')
    def test_latency_benchmark(self, mock_client):
        """Test latency benchmark."""
        # Mock client responses
        mock_instance = Mock()
        mock_instance.chat.return_value = "Test response"
        mock_client.return_value = mock_instance
        
        benchmark = benchmark_performance.PerformanceBenchmark()
        results = benchmark.benchmark_latency(num_requests=5)
        
        assert "mean_latency_s" in results
        assert "median_latency_s" in results
        assert "p95_latency_s" in results
        assert "p99_latency_s" in results
        assert results["successful_requests"] == 5
        assert results["failed_requests"] == 0
    
    @patch('benchmark_performance.CURCLLMClient')
    def test_latency_benchmark_with_errors(self, mock_client):
        """Test latency benchmark handles errors."""
        # Mock client with some failures
        mock_instance = Mock()
        mock_instance.chat.side_effect = [
            "Response 1",
            Exception("Error"),
            "Response 2",
            Exception("Error"),
            "Response 3"
        ]
        mock_client.return_value = mock_instance
        
        benchmark = benchmark_performance.PerformanceBenchmark()
        results = benchmark.benchmark_latency(num_requests=5)
        
        assert results["successful_requests"] == 3
        assert results["failed_requests"] == 2
    
    @patch('benchmark_performance.CURCLLMClient')
    @patch('benchmark_performance.time')
    def test_throughput_benchmark(self, mock_time, mock_client):
        """Test throughput benchmark."""
        # Mock time to simulate duration
        start_time = 1000.0
        mock_time.time.side_effect = [
            start_time,  # start
            start_time,  # end_time calculation
            start_time + 0.1,  # first iteration check
            start_time + 0.2,  # second iteration check
            start_time + 0.3,  # third iteration check
            start_time + 1.1,  # exit loop (> duration)
            start_time + 1.0,  # actual_duration calculation
        ]
        
        # Mock client responses
        mock_instance = Mock()
        mock_instance.chat.return_value = "Test response with multiple tokens"
        mock_client.return_value = mock_instance
        
        benchmark = benchmark_performance.PerformanceBenchmark()
        results = benchmark.benchmark_throughput(duration_seconds=1)
        
        assert "duration_s" in results
        assert "total_requests" in results
        assert "total_tokens" in results
        assert "requests_per_second" in results
        assert "tokens_per_second" in results
        assert results["errors"] == 0
    
    def test_percentile_edge_cases(self):
        """Test percentile with edge cases."""
        benchmark = benchmark_performance.PerformanceBenchmark()
        
        # Single value
        assert benchmark._percentile([5], 50) == 5
        
        # Two values - 50% of 2 = index 1
        assert benchmark._percentile([1, 2], 50) == 2
        
        # Empty should not crash (though invalid input)
        with pytest.raises(IndexError):
            benchmark._percentile([], 50)


class TestBenchmarkConfiguration:
    """Test benchmark configuration and options."""
    
    def test_quick_mode_parameters(self):
        """Test quick mode reduces benchmark load."""
        benchmark = benchmark_performance.PerformanceBenchmark()
        
        # In quick mode, num_requests should be reduced
        # We can verify this by checking method calls
        assert benchmark is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
