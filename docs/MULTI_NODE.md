# CURC LLM Hoster - Multi-Node Deployment Guide

Author: Patrick Cooper

Last Updated: 2026-02-13

## Overview

This guide explains how to deploy very large LLMs (100B+ parameters) across multiple compute nodes on CURC Alpine using Ray for distributed inference.

## When to Use Multi-Node

Use multi-node deployment when:
- Model doesn't fit on single node's GPUs (>320GB VRAM)
- Running models like Llama 3.1 405B
- Need to maximize throughput with model parallelism
- Testing extreme-scale deployments

**Single-node is recommended for most use cases** (models up to 70B with quantization).

## Architecture

Multi-node vLLM deployment uses:

1. **Ray Cluster**: Orchestrates communication between nodes
2. **Head Node**: Runs vLLM API server and Ray head
3. **Worker Nodes**: Run Ray workers with model shards
4. **Tensor Parallelism**: Splits model across GPUs
5. **Pipeline Parallelism**: Splits model layers across nodes

```
┌─────────────────────────────────────────────┐
│            CURC Alpine Cluster              │
│                                             │
│  ┌──────────────┐      ┌──────────────┐    │
│  │  Node 1      │      │  Node 2      │    │
│  │  (Head)      │◄────►│  (Worker)    │    │
│  │              │      │              │    │
│  │  Ray Head    │      │  Ray Worker  │    │
│  │  vLLM Server │      │  Model Shard │    │
│  │  Model Shard │      │              │    │
│  │              │      │              │    │
│  │  GPU 0-3     │      │  GPU 0-3     │    │
│  └──────────────┘      └──────────────┘    │
└─────────────────────────────────────────────┘
```

## Prerequisites

1. Compute allocation with multi-node access
2. Environment setup completed (`setup_environment.sh`)
3. Understanding of model parallelism concepts
4. Sufficient SU allocation for multi-node jobs

## Quick Start

### 1. Launch Multi-Node Server

Default configuration (Llama 3.1 405B on 2 nodes, 8 GPUs):

```bash
sbatch scripts/launch_vllm_multinode.slurm
```

### 2. Monitor Job

```bash
# Check job status
squeue -u $USER

# View logs
tail -f logs/vllm-multinode-<job_id>.out
```

### 3. Check Ray Cluster

The output log will show Ray cluster status:

```
Ray cluster status:
======== Autoscaler status: 2026-02-13 10:30:00 ========
Node status
---------------------------------------------------------------
Active:
 1 node_<hash> (Head)
 1 node_<hash> (Worker)
```

### 4. Get Connection Info

```bash
cat logs/multinode-connection-info-<job_id>.txt
```

This provides:
- SSH tunnel commands
- vLLM API endpoint
- Ray Dashboard URL
- Configuration details

### 5. Create SSH Tunnels

**For vLLM API:**
```bash
ssh -L 8000:<head_node>:8000 $USER@login.rc.colorado.edu
```

**For Ray Dashboard:**
```bash
ssh -L 8265:<head_node_ip>:8265 $USER@login.rc.colorado.edu
```

### 6. Query the Model

From your local machine:

```bash
python examples/interactive_chat.py
```

## Configuration

### Environment Variables

Customize deployment via environment variables:

```bash
# Model selection
MODEL_NAME="meta-llama/Llama-3.1-405B-Instruct" \
# Parallelism settings
TENSOR_PARALLEL_SIZE=8 \
PIPELINE_PARALLEL_SIZE=2 \
# Resource allocation
sbatch --nodes=2 --gres=gpu:4 scripts/launch_vllm_multinode.slurm
```

### Parallelism Configuration

**Tensor Parallelism** (splits model across GPUs on same/different nodes):
```bash
TENSOR_PARALLEL_SIZE=8  # Total GPUs for tensor parallel
```

**Pipeline Parallelism** (splits layers across nodes):
```bash
PIPELINE_PARALLEL_SIZE=2  # Number of pipeline stages
```

**Total GPUs required:**
```
Total = Tensor_Parallel × Pipeline_Parallel
```

Example: TP=8, PP=2 requires 16 GPUs (2 nodes × 8 GPUs per node)

### Common Configurations

#### Llama 3.1 405B (2 nodes, 8 GPUs)

```bash
MODEL_NAME="meta-llama/Llama-3.1-405B-Instruct" \
TENSOR_PARALLEL_SIZE=8 \
PIPELINE_PARALLEL_SIZE=2 \
sbatch --nodes=2 --gres=gpu:4 scripts/launch_vllm_multinode.slurm
```

#### Mixtral 8x22B (2 nodes, 8 GPUs)

```bash
MODEL_NAME="mistralai/Mixtral-8x22B-Instruct-v0.1" \
TENSOR_PARALLEL_SIZE=8 \
PIPELINE_PARALLEL_SIZE=1 \
sbatch --nodes=2 --gres=gpu:4 scripts/launch_vllm_multinode.slurm
```

#### Llama 3.1 70B (2 nodes, FP16 without quantization)

```bash
MODEL_NAME="meta-llama/Llama-3.1-70B-Instruct" \
TENSOR_PARALLEL_SIZE=8 \
PIPELINE_PARALLEL_SIZE=1 \
sbatch --nodes=2 --gres=gpu:4 scripts/launch_vllm_multinode.slurm
```

## Slurm Job Parameters

### Node Allocation

```bash
#SBATCH --nodes=2              # Number of compute nodes
#SBATCH --ntasks-per-node=1    # One task per node (for Ray)
#SBATCH --gres=gpu:4           # GPUs per node
```

### Time Limits

```bash
#SBATCH --time=08:00:00  # Default: 8 hours
# Or customize:
sbatch --time=24:00:00 scripts/launch_vllm_multinode.slurm
```

### Partition Selection

```bash
#SBATCH --partition=aa100  # A100 GPUs
# Or:
#SBATCH --partition=ami100  # MI100 GPUs
```

## Ray Cluster Management

### Ray Dashboard

Access Ray dashboard for monitoring:

1. Create tunnel:
```bash
ssh -L 8265:<head_node_ip>:8265 $USER@login.rc.colorado.edu
```

2. Open in browser:
```
http://localhost:8265
```

Dashboard shows:
- Cluster status
- Resource utilization
- Task execution
- Logs

### Ray Status

Check cluster status from compute node:

```bash
# SSH to head node
ssh <head_node>

# Activate environment
source vllm-env/bin/activate

# Check status
ray status
```

### Manual Ray Management

If needed, manually control Ray:

```bash
# Stop Ray
ray stop

# Start Ray head
ray start --head --port=6379

# Start Ray worker
ray start --address=<head_ip>:6379
```

## Performance Optimization

### Network Performance

Multi-node performance depends on inter-node network:

**CURC Alpine Network:**
- InfiniBand for high-speed inter-node communication
- Low latency (<5μs)
- High bandwidth (100+ Gbps)

**Optimization:**
- Use `--gres=gpu:4` to get GPUs on same node first
- Minimize pipeline parallel stages when possible
- Use larger batch sizes to amortize communication

### Memory Management

```bash
# Reduce per-GPU memory if OOM
GPU_MEMORY_UTILIZATION=0.85 \
sbatch scripts/launch_vllm_multinode.slurm
```

### Context Length

```bash
# Reduce max context for memory savings
MAX_MODEL_LEN=2048 \
sbatch scripts/launch_vllm_multinode.slurm
```

## Troubleshooting

### Ray Cluster Won't Start

**Symptoms:** Workers fail to connect to head

**Solutions:**
1. Check network connectivity between nodes
2. Verify firewall allows Ray ports (6379, 8265)
3. Check head node IP is correct
4. Increase sleep time between node starts

### Out of Memory

**Symptoms:** CUDA OOM error

**Solutions:**
1. Reduce `GPU_MEMORY_UTILIZATION`
2. Reduce `MAX_MODEL_LEN`
3. Increase tensor parallelism (use more GPUs)
4. Use quantized model instead

### Slow Performance

**Symptoms:** Lower throughput than expected

**Diagnosis:**
```bash
# Check GPU utilization on all nodes
pdsh -w <node_list> nvidia-smi
```

**Solutions:**
1. Increase batch size
2. Reduce pipeline parallelism if possible
3. Check network is not saturated
4. Verify all GPUs are being used

### Job Pending

**Symptoms:** Job stays in queue

**Solutions:**
1. Reduce number of nodes requested
2. Reduce time limit
3. Check allocation balance: `mybalance`
4. Try different partition

## Cost Management

### Service Unit Calculation

Multi-node jobs consume SUs rapidly:

```
SUs = hours × nodes × gpus_per_node × 108.6
```

Example: 2 nodes, 4 GPUs each, 8 hours:
```
SUs = 8 × 2 × 4 × 108.6 = 6,950 SUs
```

### Cost Optimization

1. **Test with smaller configs first**
   - Use single-node quantized models for development
   - Only use multi-node for production/final testing

2. **Set appropriate time limits**
   - Don't request more time than needed
   - Use `--time=` flag to set exactly what you need

3. **Use checkpointing**
   - For long-running inference jobs
   - Save progress periodically

4. **Monitor usage**
   ```bash
   mybalance  # Check remaining SUs
   ```

## Best Practices

1. **Start Small**
   - Test with 2 nodes before scaling to more
   - Verify single-node deployment first

2. **Monitor Logs**
   - Watch Ray cluster formation
   - Check for errors early
   - Use `tail -f` on log files

3. **Save Connection Info**
   - Connection info files are auto-generated
   - Reference them for SSH tunnels

4. **Clean Shutdown**
   - Ray cleanup is automatic on job end
   - Cancel jobs properly: `scancel <job_id>`

5. **Document Configuration**
   - Save working configurations
   - Note performance characteristics
   - Track SU consumption

## Advanced Topics

### Custom Ray Configuration

Edit the script to customize Ray:

```bash
ray start --head \
  --num-cpus=64 \
  --num-gpus=4 \
  --object-store-memory=50000000000
```

### Mixed Precision

```bash
# Use FP8 for some layers
MIXED_PRECISION=true \
sbatch scripts/launch_vllm_multinode.slurm
```

### Multi-Node Benchmarking

```bash
# After starting multi-node server
python scripts/benchmark_performance.py \
  --mode full \
  --output multinode_benchmark.json
```

## Comparison: Single-Node vs Multi-Node

| Aspect | Single-Node | Multi-Node |
|--------|-------------|------------|
| Max Model Size | ~70B (quantized) | 405B+ (FP16) |
| Setup Complexity | Simple | Complex |
| Performance | Faster (no network overhead) | Slower (network communication) |
| Cost (SUs) | Lower | Higher (2-10x) |
| Best For | Most use cases | Largest models only |

## Example Workflow

```bash
# 1. Setup (one-time)
./scripts/setup_environment.sh

# 2. Launch multi-node server
MODEL_NAME="meta-llama/Llama-3.1-405B-Instruct" \
sbatch --nodes=2 --gres=gpu:4 scripts/launch_vllm_multinode.slurm

# 3. Get job ID
squeue -u $USER
# Note job ID: 123456

# 4. Monitor startup
tail -f logs/vllm-multinode-123456.out

# 5. Get connection info (once running)
cat logs/multinode-connection-info-123456.txt

# 6. Create tunnels (on local machine)
ssh -L 8000:<head_node>:8000 $USER@login.rc.colorado.edu

# 7. Use the model
python examples/interactive_chat.py

# 8. Monitor performance
# Open Ray dashboard: http://localhost:8265

# 9. Cleanup
scancel 123456
```

## Getting Help

For multi-node specific issues:
- Ray documentation: https://docs.ray.io/
- vLLM distributed serving: https://docs.vllm.ai/en/latest/serving/distributed_serving.html
- CURC support: rc-help@colorado.edu
