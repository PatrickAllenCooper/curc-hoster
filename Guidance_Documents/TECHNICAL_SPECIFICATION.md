# CURC LLM Hosting - Technical Specification

Author: Patrick Cooper

Last Updated: 2026-02-13

## Overview

This document provides the technical specification for deploying Large Language Model (LLM) inference infrastructure on University of Colorado Boulder Research Computing (CURC) resources using vLLM and Ray.

## Architecture Decision

### Why vLLM over Alternatives

Based on comprehensive research and benchmarking:

**vLLM** selected as the primary serving framework:
- **Performance**: Achieves 793 tokens/second vs Ollama's 41 TPS on A100 GPU
- **Latency**: P99 latency of 80ms vs Ollama's 673ms
- **Memory Efficiency**: PagedAttention reduces KV cache fragmentation by 60-80%
- **Scalability**: Native support for multi-GPU and multi-node deployments
- **Production-Ready**: Powers inference at Meta, Mistral AI, Cohere, and IBM
- **API Compatibility**: OpenAI-compatible REST API for easy integration

**Rejected Alternatives**:
- **Ollama**: Excellent for local development but underperforms at scale (1-4 users max)
- **HuggingFace TGI**: Better for single-user latency but 24x lower throughput under load
- **Native HF Transformers**: No built-in serving, batching, or optimization features

### CURC-Specific Considerations

**Cluster Selection**: Alpine (primary)
- Tiered allocation system: Trailhead (auto), Ascent (350K SUs), Peak (350K-6M SUs)
- GPU acceleration factors: A100/L40/MI100 = 108.6x CPU speedup for FairShare
- Slurm workload manager with FairShare scheduling
- Pre-installed LLM models accessible via `$CURC_LLM_DIR`

**GPU Resources**:
- NVIDIA A100 (80GB): Optimal for 70B parameter models
- NVIDIA L40 (48GB): Suitable for 13B-34B parameter models
- AMD MI100: Alternative accelerator option

## System Architecture

### Deployment Topology

```
┌─────────────────────────────────────────────────────┐
│                 CURC Alpine Cluster                 │
│                                                     │
│  ┌──────────────┐         ┌──────────────┐        │
│  │  Head Node   │         │ Worker Node  │        │
│  │              │         │              │        │
│  │  Ray Head    │◄───────►│  Ray Worker  │        │
│  │  vLLM Server │         │  vLLM Engine │        │
│  │              │         │              │        │
│  │  GPU 0-3     │         │  GPU 0-3     │        │
│  └──────────────┘         └──────────────┘        │
│         │                                          │
│         │ OpenAI-compatible API                    │
│         ▼                                          │
│  ┌──────────────┐                                 │
│  │  Client Apps │                                 │
│  └──────────────┘                                 │
└─────────────────────────────────────────────────────┘
```

### Key Components

1. **Slurm Job Scripts**: Allocate GPU resources and launch vLLM
2. **Ray Cluster**: Orchestrate distributed inference across nodes
3. **vLLM Server**: High-performance inference engine with PagedAttention
4. **REST API**: OpenAI-compatible endpoints (chat completions, completions)
5. **Model Management**: Load models from Hugging Face Hub or local cache

## Technical Implementation

### Parallelism Strategies

**Tensor Parallelism** (single model split across GPUs):
- Use for models that don't fit on single GPU
- Example: Llama 3.1 70B across 4x A100 (80GB each)
- Configure via `tensor_parallel_size` parameter

**Pipeline Parallelism** (model layers across nodes):
- Use for extremely large models (100B+ parameters)
- Combine with tensor parallelism for Llama 3.1 405B
- Configure via `pipeline_parallel_size` parameter

**Data Parallelism** (multiple model replicas):
- Automatic load balancing across requests
- Increases throughput for high-concurrency scenarios

### Memory Requirements

| Model Size | Quantization | VRAM Required | GPU Configuration |
|-----------|--------------|---------------|-------------------|
| 7B-8B     | FP16        | ~16 GB       | 1x L40           |
| 13B       | FP16        | ~26 GB       | 1x A100          |
| 34B       | FP16        | ~68 GB       | 1x A100          |
| 70B       | FP16        | ~140 GB      | 2x A100 (80GB)   |
| 405B      | FP16        | ~810 GB      | 10x A100 (80GB)  |

With INT4/INT8 quantization, VRAM requirements reduced by 50-75%.

### Performance Optimization

**PagedAttention**:
- Treats GPU memory like virtual memory
- Eliminates 60-80% of memory fragmentation
- Enables 2-24x throughput improvement

**Continuous Batching**:
- Dynamically merges incoming requests
- Maximizes GPU utilization
- Reduces average latency for batch workloads

**KV Cache Management**:
- Automatic cache eviction policies
- Configurable cache size limits
- Prefix caching for repeated prompts

## Deployment Workflow

### Phase 1: Environment Setup
1. Load required modules on CURC Alpine
2. Create Python virtual environment
3. Install vLLM, Ray, and dependencies
4. Configure Hugging Face authentication token

### Phase 2: Single-Node Deployment
1. Write Slurm batch script for single-node job
2. Launch vLLM server with desired model
3. Verify API endpoint accessibility
4. Run basic inference tests

### Phase 3: Multi-Node Scaling
1. Create Ray cluster configuration
2. Write Slurm script for multi-node allocation
3. Launch Ray head on first node
4. Connect Ray workers on additional nodes
5. Start distributed vLLM inference

### Phase 4: Production Hardening
1. Implement authentication and access control
2. Add request logging and metrics collection
3. Configure automatic restart on failure
4. Set up monitoring dashboards
5. Document operational procedures

## API Specification

### Endpoints

**Chat Completions** (recommended):
```
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing."}
  ],
  "temperature": 0.7,
  "max_tokens": 512
}
```

**Completions** (legacy):
```
POST /v1/completions
Content-Type: application/json

{
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "prompt": "The future of AI is",
  "max_tokens": 100,
  "temperature": 0.8
}
```

### Authentication

Implement via API keys:
- Set `--api-key` parameter when launching vLLM
- Include `Authorization: Bearer <key>` header in requests
- Support multiple keys for different users/projects

## Resource Allocation Guidelines

### Service Unit Estimation

On Alpine, GPU jobs consume SUs based on:
```
SUs = wall_time_hours × num_gpus × gpu_acceleration_factor
```

For A100 GPU: `SUs = hours × gpus × 108.6`

Examples:
- 1 A100 for 24 hours: 24 × 1 × 108.6 = 2,606 SUs
- 4 A100 for 8 hours: 8 × 4 × 108.6 = 3,475 SUs
- Ascent allocation (350K SUs): ~134 hours of 1x A100 usage

### Job Scheduling Best Practices

1. **Request appropriate time limits**: Avoid overestimating walltime
2. **Use checkpointing**: Save model state for long-running jobs
3. **Monitor FairShare**: Balance usage to maintain priority
4. **Batch requests**: Maximize GPU utilization per job
5. **Test on smaller allocations**: Validate before large-scale runs

## Testing Strategy

### Unit Tests
- Model loading and initialization
- API endpoint response validation
- Tensor parallelism configuration
- Error handling and edge cases

### Integration Tests
- End-to-end inference pipeline
- Multi-GPU coordination
- Ray cluster communication
- Slurm job submission and monitoring

### Performance Tests
- Throughput benchmarking (tokens/second)
- Latency profiling (P50, P95, P99)
- Concurrent user load testing
- Memory utilization analysis

### Acceptance Criteria
- All unit tests pass with >90% code coverage
- API returns valid responses for all supported models
- Throughput exceeds 500 tokens/second on single A100
- P99 latency remains below 100ms for interactive queries
- Multi-GPU tensor parallelism verified for 70B model

## Monitoring and Observability

### Metrics to Track
- Requests per second (RPS)
- Tokens per second (TPS)
- Request latency distribution (P50, P95, P99)
- GPU utilization percentage
- GPU memory usage
- KV cache hit rate
- Queue depth and wait time

### Logging
- Request logs (timestamp, model, tokens, latency)
- Error logs (failures, timeouts, OOM events)
- System logs (GPU stats, Ray cluster status)

### Tools
- vLLM built-in metrics endpoint (`/metrics`)
- Ray dashboard for cluster visualization
- Slurm accounting tools (`sacct`, `squeue`)
- Custom dashboards (Grafana/Prometheus optional)

## Security Considerations

### Data Privacy
- All inference runs locally on CURC infrastructure
- No external API calls or data exfiltration
- Comply with CU's AI guidance and CURC policies

### Access Control
- API key authentication for production deployments
- Network isolation within CURC environment
- Audit logging for all API requests

### Model Provenance
- Download models only from trusted sources (Hugging Face, official repos)
- Verify model checksums before deployment
- Document model licenses and usage restrictions

## Maintenance and Operations

### Model Updates
1. Download new model version to shared storage
2. Test in development environment
3. Update deployment configuration
4. Restart vLLM server with new model
5. Validate API responses

### Troubleshooting Common Issues

**Out of Memory (OOM)**:
- Reduce `max_num_seqs` or `max_model_len`
- Enable quantization (INT8/INT4)
- Increase tensor parallelism size

**Slow Performance**:
- Check GPU utilization (should be >80%)
- Increase batch size via `max_num_batched_tokens`
- Reduce concurrent requests if queue is saturated

**Ray Cluster Connection Issues**:
- Verify network connectivity between nodes
- Check Ray head node IP and port
- Ensure firewall rules allow Ray ports (6379, 8265)

## Future Enhancements

### Short-Term (Next 3 Months)
- Automated model download and caching
- Request queue management with priorities
- Enhanced error handling and retry logic
- Comprehensive user documentation

### Medium-Term (3-6 Months)
- Support for LoRA adapter serving
- Multi-model serving (switch between models)
- Advanced batching strategies
- Cost tracking and allocation reporting

### Long-Term (6+ Months)
- Automatic scaling based on demand
- Integration with CURC's Open OnDemand portal
- Fine-tuning pipeline integration
- Community model repository

## References

### CURC Documentation
- [Running Large Language Models](https://curc.readthedocs.io/en/latest/ai-ml/llms.html)
- [Alpine Allocations](https://curc.readthedocs.io/en/latest/clusters/alpine/allocations.html)
- [Blanca Condo Cluster](https://curc.readthedocs.io/en/latest/clusters/blanca/blanca.html)

### vLLM Documentation
- [vLLM Distributed Serving](https://docs.vllm.ai/en/latest/serving/distributed_serving.html)
- [vLLM Run Cluster](https://docs.vllm.ai/en/latest/examples/online_serving/run_cluster/)

### Research Papers
- PagedAttention: [arXiv:2309.06180](https://arxiv.org/abs/2309.06180)
- vLLM vs TGI Comparison: [arXiv:2511.17593](https://arxiv.org/abs/2511.17593)

### Community Resources
- [Stanford Ollama on HPC](https://rcpedia.stanford.edu/blog/2025/05/12/running-ollama-on-stanford-computing-clusters/)
- [Yale LLMs on Research Computing](https://docs.ycrc.yale.edu/clusters-at-yale/guides/LLMs/)
- [vLLM Production Deployment](https://introl.com/blog/vllm-production-deployment-inference-serving-architecture)
