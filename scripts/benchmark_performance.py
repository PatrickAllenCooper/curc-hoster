#!/usr/bin/env python3
"""
CURC LLM Performance Benchmarking Suite

Author: Patrick Cooper

Benchmarks throughput, latency, and concurrency for vLLM deployments.
"""

import argparse
import asyncio
import json
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.curc_llm_client import CURCLLMClient


class PerformanceBenchmark:
    """Performance benchmarking for vLLM servers."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """Initialize benchmark suite."""
        self.base_url = base_url
        self.api_key = api_key
        self.results = {}
    
    def benchmark_latency(
        self,
        num_requests: int = 100,
        prompt: str = "Write a short paragraph about artificial intelligence.",
        max_tokens: int = 100
    ) -> Dict[str, float]:
        """
        Benchmark single-request latency.
        
        Args:
            num_requests: Number of sequential requests
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary of latency statistics
        """
        print(f"\n{'='*60}")
        print("LATENCY BENCHMARK")
        print(f"{'='*60}")
        print(f"Requests: {num_requests}")
        print(f"Max tokens: {max_tokens}")
        print(f"Prompt length: {len(prompt.split())} words\n")
        
        client = CURCLLMClient(base_url=self.base_url, api_key=self.api_key)
        latencies = []
        
        for i in range(num_requests):
            start_time = time.time()
            try:
                response = client.chat(prompt, max_tokens=max_tokens)
                latency = time.time() - start_time
                latencies.append(latency)
                
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{num_requests} requests")
            
            except Exception as e:
                print(f"  Error on request {i+1}: {e}")
        
        if not latencies:
            return {"error": "No successful requests"}
        
        results = {
            "mean_latency_s": statistics.mean(latencies),
            "median_latency_s": statistics.median(latencies),
            "p95_latency_s": self._percentile(latencies, 95),
            "p99_latency_s": self._percentile(latencies, 99),
            "min_latency_s": min(latencies),
            "max_latency_s": max(latencies),
            "std_dev_s": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "successful_requests": len(latencies),
            "failed_requests": num_requests - len(latencies)
        }
        
        print(f"\nResults:")
        print(f"  Mean latency: {results['mean_latency_s']:.3f}s")
        print(f"  Median latency: {results['median_latency_s']:.3f}s")
        print(f"  P95 latency: {results['p95_latency_s']:.3f}s")
        print(f"  P99 latency: {results['p99_latency_s']:.3f}s")
        print(f"  Min/Max: {results['min_latency_s']:.3f}s / {results['max_latency_s']:.3f}s")
        
        return results
    
    def benchmark_throughput(
        self,
        duration_seconds: int = 60,
        prompt: str = "Explain the concept of machine learning.",
        max_tokens: int = 100
    ) -> Dict[str, float]:
        """
        Benchmark sustained throughput.
        
        Args:
            duration_seconds: How long to run the benchmark
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary of throughput statistics
        """
        print(f"\n{'='*60}")
        print("THROUGHPUT BENCHMARK")
        print(f"{'='*60}")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Max tokens: {max_tokens}\n")
        
        client = CURCLLMClient(base_url=self.base_url, api_key=self.api_key)
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        request_count = 0
        total_tokens = 0
        errors = 0
        
        print("Running...")
        while time.time() < end_time:
            try:
                response = client.chat(prompt, max_tokens=max_tokens)
                request_count += 1
                # Approximate tokens (actual count would require tokenizer)
                total_tokens += len(response.split())
                
                if request_count % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"  {request_count} requests in {elapsed:.1f}s")
            
            except Exception as e:
                errors += 1
                if errors < 5:  # Only print first few errors
                    print(f"  Error: {e}")
        
        actual_duration = time.time() - start_time
        
        results = {
            "duration_s": actual_duration,
            "total_requests": request_count,
            "total_tokens": total_tokens,
            "requests_per_second": request_count / actual_duration,
            "tokens_per_second": total_tokens / actual_duration,
            "errors": errors,
            "avg_tokens_per_request": total_tokens / request_count if request_count > 0 else 0
        }
        
        print(f"\nResults:")
        print(f"  Total requests: {results['total_requests']}")
        print(f"  Total tokens: {results['total_tokens']}")
        print(f"  Requests/second: {results['requests_per_second']:.2f}")
        print(f"  Tokens/second: {results['tokens_per_second']:.2f}")
        print(f"  Errors: {results['errors']}")
        
        return results
    
    async def _concurrent_request(
        self,
        client: CURCLLMClient,
        prompt: str,
        max_tokens: int,
        request_id: int
    ) -> Dict[str, Any]:
        """Make a single concurrent request."""
        start_time = time.time()
        try:
            # Note: Using sync client in async context - for true async would need async client
            response = await asyncio.to_thread(
                client.chat,
                prompt,
                max_tokens=max_tokens
            )
            latency = time.time() - start_time
            return {
                "success": True,
                "latency": latency,
                "tokens": len(response.split()),
                "request_id": request_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency": time.time() - start_time,
                "request_id": request_id
            }
    
    async def benchmark_concurrency_async(
        self,
        num_concurrent: int = 10,
        num_requests_per_client: int = 5,
        prompt: str = "Describe a sunset.",
        max_tokens: int = 50
    ) -> Dict[str, Any]:
        """
        Benchmark concurrent request handling (async version).
        
        Args:
            num_concurrent: Number of concurrent clients
            num_requests_per_client: Requests per client
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary of concurrency statistics
        """
        print(f"\n{'='*60}")
        print("CONCURRENCY BENCHMARK")
        print(f"{'='*60}")
        print(f"Concurrent clients: {num_concurrent}")
        print(f"Requests per client: {num_requests_per_client}")
        print(f"Total requests: {num_concurrent * num_requests_per_client}\n")
        
        client = CURCLLMClient(base_url=self.base_url, api_key=self.api_key)
        
        print("Launching concurrent requests...")
        start_time = time.time()
        
        # Create tasks for all requests
        tasks = []
        request_id = 0
        for _ in range(num_concurrent):
            for _ in range(num_requests_per_client):
                task = self._concurrent_request(client, prompt, max_tokens, request_id)
                tasks.append(task)
                request_id += 1
        
        # Execute all concurrently
        results_list = await asyncio.gather(*tasks)
        
        total_duration = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results_list if r["success"]]
        failed = [r for r in results_list if not r["success"]]
        
        if successful:
            latencies = [r["latency"] for r in successful]
            total_tokens = sum(r["tokens"] for r in successful)
            
            results = {
                "total_duration_s": total_duration,
                "total_requests": len(results_list),
                "successful_requests": len(successful),
                "failed_requests": len(failed),
                "mean_latency_s": statistics.mean(latencies),
                "median_latency_s": statistics.median(latencies),
                "p95_latency_s": self._percentile(latencies, 95),
                "p99_latency_s": self._percentile(latencies, 99),
                "total_tokens": total_tokens,
                "overall_throughput_rps": len(successful) / total_duration,
                "overall_throughput_tps": total_tokens / total_duration,
                "concurrent_clients": num_concurrent
            }
        else:
            results = {
                "error": "All requests failed",
                "failed_requests": len(failed),
                "errors": [r.get("error") for r in failed[:5]]  # First 5 errors
            }
        
        print(f"\nResults:")
        if "error" not in results:
            print(f"  Successful: {results['successful_requests']}/{results['total_requests']}")
            print(f"  Total duration: {results['total_duration_s']:.2f}s")
            print(f"  Mean latency: {results['mean_latency_s']:.3f}s")
            print(f"  P99 latency: {results['p99_latency_s']:.3f}s")
            print(f"  Throughput: {results['overall_throughput_tps']:.2f} tokens/s")
        else:
            print(f"  ERROR: {results['error']}")
            print(f"  Sample errors: {results.get('errors', [])}")
        
        return results
    
    def benchmark_concurrency(self, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for concurrency benchmark."""
        return asyncio.run(self.benchmark_concurrency_async(**kwargs))
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def run_full_benchmark(
        self,
        output_file: str = None,
        quick: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete benchmark suite.
        
        Args:
            output_file: Path to save results JSON
            quick: If True, run abbreviated benchmarks
            
        Returns:
            Complete benchmark results
        """
        print(f"\n{'#'*60}")
        print("CURC LLM PERFORMANCE BENCHMARK SUITE")
        print(f"{'#'*60}")
        print(f"Server: {self.base_url}")
        print(f"Mode: {'Quick' if quick else 'Full'}")
        print(f"Started: {datetime.now().isoformat()}")
        
        all_results = {
            "metadata": {
                "server": self.base_url,
                "timestamp": datetime.now().isoformat(),
                "mode": "quick" if quick else "full"
            }
        }
        
        try:
            # Latency benchmark
            if quick:
                all_results["latency"] = self.benchmark_latency(num_requests=20)
            else:
                all_results["latency"] = self.benchmark_latency(num_requests=100)
            
            # Throughput benchmark
            if quick:
                all_results["throughput"] = self.benchmark_throughput(duration_seconds=30)
            else:
                all_results["throughput"] = self.benchmark_throughput(duration_seconds=60)
            
            # Concurrency benchmark
            if quick:
                all_results["concurrency"] = self.benchmark_concurrency(
                    num_concurrent=5,
                    num_requests_per_client=3
                )
            else:
                all_results["concurrency"] = self.benchmark_concurrency(
                    num_concurrent=10,
                    num_requests_per_client=5
                )
            
            all_results["status"] = "completed"
        
        except Exception as e:
            all_results["status"] = "failed"
            all_results["error"] = str(e)
            print(f"\nBenchmark failed: {e}")
        
        # Save results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"\nResults saved to: {output_file}")
        
        print(f"\n{'#'*60}")
        print("BENCHMARK COMPLETE")
        print(f"{'#'*60}\n")
        
        return all_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Performance benchmarking for CURC LLM deployments"
    )
    
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of vLLM server (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key for authentication"
    )
    
    parser.add_argument(
        "--mode",
        choices=["latency", "throughput", "concurrency", "full"],
        default="full",
        help="Benchmark mode (default: full)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run abbreviated benchmarks"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for results (JSON)"
    )
    
    parser.add_argument(
        "--num-requests",
        type=int,
        default=100,
        help="Number of requests for latency benchmark"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration in seconds for throughput benchmark"
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent clients"
    )
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(
        base_url=args.base_url,
        api_key=args.api_key
    )
    
    if args.mode == "full":
        results = benchmark.run_full_benchmark(
            output_file=args.output,
            quick=args.quick
        )
    elif args.mode == "latency":
        results = benchmark.benchmark_latency(num_requests=args.num_requests)
    elif args.mode == "throughput":
        results = benchmark.benchmark_throughput(duration_seconds=args.duration)
    elif args.mode == "concurrency":
        results = benchmark.benchmark_concurrency(num_concurrent=args.concurrent)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
