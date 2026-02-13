# CURC LLM Hoster - Performance Benchmarking Guide

Author: Patrick Cooper

Last Updated: 2026-02-13

## Overview

This guide explains how to benchmark the performance of vLLM deployments on CURC infrastructure, measuring throughput, latency, and concurrency handling.

## Benchmarking Tool

The `scripts/benchmark_performance.py` tool provides comprehensive performance testing:

- **Latency Benchmarks**: Measure single-request response times
- **Throughput Benchmarks**: Measure sustained tokens/second
- **Concurrency Benchmarks**: Test multi-user concurrent access

## Prerequisites

1. Running vLLM server on CURC (via Slurm job)
2. Active SSH tunnel to server
3. Python dependencies installed locally (`pip install -r requirements.txt`)

## Quick Start

### Basic Benchmark

Run complete benchmark suite:

```bash
python scripts/benchmark_performance.py --base-url http://localhost:8000
```

### Quick Benchmark

Abbreviated version for faster results:

```bash
python scripts/benchmark_performance.py --quick
```

### Specific Benchmark Types

**Latency only**:
```bash
python scripts/benchmark_performance.py --mode latency --num-requests 100
```

**Throughput only**:
```bash
python scripts/benchmark_performance.py --mode throughput --duration 60
```

**Concurrency only**:
```bash
python scripts/benchmark_performance.py --mode concurrency --concurrent 10
```

## Benchmark Types

### 1. Latency Benchmark

Measures response time for sequential single requests.

**Metrics Reported:**
- Mean latency
- Median latency
- P95 latency (95th percentile)
- P99 latency (99th percentile)
- Min/Max latency
- Standard deviation

**Parameters:**
- `--num-requests`: Number of sequential requests (default: 100)

**Example:**
```bash
python scripts/benchmark_performance.py \
  --mode latency \
  --num-requests 200 \
  --output latency_results.json
```

**Expected Results (A100, Llama 3.1 8B):**
- Mean latency: 0.5-2.0s
- P99 latency: <3.0s

### 2. Throughput Benchmark

Measures sustained generation rate over time.

**Metrics Reported:**
- Total requests completed
- Total tokens generated
- Requests per second
- Tokens per second
- Average tokens per request
- Error count

**Parameters:**
- `--duration`: Benchmark duration in seconds (default: 60)

**Example:**
```bash
python scripts/benchmark_performance.py \
  --mode throughput \
  --duration 120 \
  --output throughput_results.json
```

**Expected Results (A100, Llama 3.1 8B):**
- Throughput: 500-800 tokens/second
- Requests/second: 5-10 (depends on max_tokens)

### 3. Concurrency Benchmark

Tests performance under concurrent multi-user load.

**Metrics Reported:**
- Total duration
- Successful/failed requests
- Mean/median/P95/P99 latency under load
- Overall throughput (tokens/second)
- Concurrent clients handled

**Parameters:**
- `--concurrent`: Number of concurrent clients (default: 10)

**Example:**
```bash
python scripts/benchmark_performance.py \
  --mode concurrency \
  --concurrent 20 \
  --output concurrency_results.json
```

**Expected Results (A100, Llama 3.1 8B):**
- 10 concurrent: P99 < 5s
- 20 concurrent: P99 < 10s
- Throughput: 400-600 tokens/second

## Full Benchmark Suite

### Standard Mode

Comprehensive benchmarking (~3-5 minutes):

```bash
python scripts/benchmark_performance.py \
  --mode full \
  --output benchmark_results.json
```

**Includes:**
- 100 latency requests
- 60 second throughput test
- 10 concurrent clients × 5 requests each

### Quick Mode

Abbreviated benchmarking (~1-2 minutes):

```bash
python scripts/benchmark_performance.py \
  --mode full \
  --quick \
  --output quick_benchmark.json
```

**Includes:**
- 20 latency requests
- 30 second throughput test
- 5 concurrent clients × 3 requests each

## Output Format

Results are saved as JSON:

```json
{
  "metadata": {
    "server": "http://localhost:8000",
    "timestamp": "2026-02-13T10:30:00",
    "mode": "full"
  },
  "latency": {
    "mean_latency_s": 1.234,
    "median_latency_s": 1.156,
    "p95_latency_s": 2.345,
    "p99_latency_s": 3.456,
    "successful_requests": 100,
    "failed_requests": 0
  },
  "throughput": {
    "duration_s": 60.0,
    "total_requests": 450,
    "total_tokens": 45000,
    "requests_per_second": 7.5,
    "tokens_per_second": 750.0,
    "errors": 0
  },
  "concurrency": {
    "total_duration_s": 15.6,
    "successful_requests": 50,
    "mean_latency_s": 2.1,
    "p99_latency_s": 4.5,
    "overall_throughput_tps": 640.2,
    "concurrent_clients": 10
  },
  "status": "completed"
}
```

## Performance Targets

### Single A100 80GB

**Llama 3.1 8B (FP16):**
- Throughput: 500-800 TPS
- P99 Latency: <2s
- Concurrent users: 10-20

**Qwen 2.5 72B (AWQ):**
- Throughput: 200-400 TPS
- P99 Latency: <3s
- Concurrent users: 5-10

**Llama 3.3 70B (AWQ):**
- Throughput: 200-400 TPS
- P99 Latency: <3s
- Concurrent users: 5-10

### Multi-GPU (4x A100)

**Llama 3.1 70B (FP16):**
- Throughput: 400-600 TPS
- P99 Latency: <2s
- Concurrent users: 20-40

## Interpreting Results

### Good Performance Indicators

- P99 latency less than 100ms for interactive queries
- Throughput greater than 500 TPS for 8B models
- Error rate less than 1%
- Linear scaling with concurrent users (up to saturation)

### Performance Issues

- P99 latency greater than 5s: Check GPU utilization, increase resources
- Throughput less than 200 TPS: Model too large, consider quantization
- Errors greater than 5%: Server overloaded or configuration issues
- Latency increases exponentially with users: Need more GPUs

## Optimization Tips

### For Better Latency

1. Reduce `max_model_len`
2. Lower `max_num_seqs`
3. Use smaller model
4. Increase `gpu_memory_utilization`

### For Better Throughput

1. Increase `max_num_batched_tokens`
2. Increase `max_num_seqs`
3. Use continuous batching (default in vLLM)
4. Process requests in batches

### For Better Concurrency

1. Increase tensor parallelism (more GPUs)
2. Optimize batching parameters
3. Use smaller max_tokens per request
4. Consider using quantized models

## Common Benchmarking Scenarios

### Scenario 1: Production Deployment Validation

Before deploying to users:

```bash
# Full benchmark suite
python scripts/benchmark_performance.py \
  --mode full \
  --output production_benchmark.json

# Verify results meet targets
# - P99 latency < target SLA
# - Throughput sufficient for expected load
# - Error rate < 1%
```

### Scenario 2: Model Comparison

Compare different models:

```bash
# Benchmark model A
python scripts/benchmark_performance.py \
  --quick \
  --output model_a_benchmark.json

# Switch to model B (restart server)
# Then benchmark model B
python scripts/benchmark_performance.py \
  --quick \
  --output model_b_benchmark.json

# Compare results
```

### Scenario 3: Configuration Tuning

Test different vLLM configurations:

```bash
# Test configuration 1
# Launch server with config 1
python scripts/benchmark_performance.py --quick --output config1.json

# Test configuration 2
# Restart server with config 2
python scripts/benchmark_performance.py --quick --output config2.json

# Compare to find optimal settings
```

### Scenario 4: Capacity Planning

Determine maximum concurrent users:

```bash
# Test increasing concurrency
for concurrent in 5 10 20 40 80; do
  python scripts/benchmark_performance.py \
    --mode concurrency \
    --concurrent $concurrent \
    --output capacity_${concurrent}.json
done

# Analyze where performance degrades
```

## Troubleshooting

### Benchmark Fails to Connect

```
Error: Connection refused
```

**Solution:**
1. Verify vLLM server is running: `squeue -u $USER`
2. Check SSH tunnel is active: `lsof -i :8000`
3. Test health endpoint: `curl http://localhost:8000/health`

### High Error Rates

```
failed_requests: 45/50
```

**Solutions:**
1. Server overloaded → reduce concurrency
2. Timeout too short → increase timeout
3. Model OOM → reduce max_tokens or use smaller model

### Inconsistent Results

**Solutions:**
1. Run benchmark multiple times and average
2. Ensure server is warmed up (run a few requests first)
3. Check for competing jobs on GPU
4. Verify network stability

### Low Throughput

**Diagnosis:**
```bash
# Check GPU utilization during benchmark
# On CURC compute node:
nvidia-smi dmon -s u
```

**Solutions:**
- GPU util < 50%: Increase batch size
- GPU util > 95%: Good, already optimized
- High memory usage: Reduce model size or quantize

## Advanced Usage

### Custom Prompts

```python
from scripts.benchmark_performance import PerformanceBenchmark

benchmark = PerformanceBenchmark()

# Custom latency test
results = benchmark.benchmark_latency(
    num_requests=50,
    prompt="Your custom prompt here",
    max_tokens=200
)
```

### Programmatic Use

```python
from scripts.benchmark_performance import PerformanceBenchmark

benchmark = PerformanceBenchmark(base_url="http://localhost:8000")

# Run individual benchmarks
latency = benchmark.benchmark_latency(num_requests=100)
throughput = benchmark.benchmark_throughput(duration_seconds=60)
concurrency = benchmark.benchmark_concurrency(num_concurrent=10)

# Access results
print(f"P99 Latency: {latency['p99_latency_s']:.3f}s")
print(f"Throughput: {throughput['tokens_per_second']:.2f} TPS")
```

### Automated Regression Testing

```bash
#!/bin/bash
# Run benchmarks and check against baselines

python scripts/benchmark_performance.py --quick --output current.json

# Compare with baseline
python -c "
import json
current = json.load(open('current.json'))
baseline = json.load(open('baseline.json'))

tps_current = current['throughput']['tokens_per_second']
tps_baseline = baseline['throughput']['tokens_per_second']

if tps_current < tps_baseline * 0.9:
    print(f'REGRESSION: TPS dropped from {tps_baseline} to {tps_current}')
    exit(1)
else:
    print('PASS: Performance maintained')
"
```

## Best Practices

1. **Warm up the server** with a few requests before benchmarking
2. **Run multiple iterations** and report average
3. **Document configuration** with each benchmark
4. **Save all results** for historical comparison
5. **Test realistic workloads** matching production use
6. **Monitor GPU metrics** during benchmarking
7. **Isolate variables** when comparing configurations
8. **Use consistent prompts** for reproducibility

## References

- vLLM Performance Guide: https://docs.vllm.ai/en/latest/performance/
- Paper.tex: Project performance goals
- TECHNICAL_SPECIFICATION.md: Architecture details
