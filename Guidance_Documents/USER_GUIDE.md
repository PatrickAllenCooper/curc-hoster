# CURC LLM Hoster - User Guide

Author: Patrick Cooper

Last Updated: 2026-02-13

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Setup](#detailed-setup)
5. [Usage Examples](#usage-examples)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Topics](#advanced-topics)

## Introduction

This guide walks you through deploying and using LLM inference servers on CURC Alpine cluster and querying them from your local machine using an OpenAI-compatible API.

### What You'll Accomplish

- Deploy a vLLM inference server on CURC Alpine
- Create an SSH tunnel to access the server from your local machine
- Query the LLM using a Python client SDK
- Run interactive chat sessions with the hosted model

### Architecture Overview

```
Your Local Machine          CURC Alpine Cluster
┌─────────────────┐        ┌──────────────────┐
│                 │  SSH   │  Compute Node    │
│  Python Client  │◄──────►│                  │
│  (port 8000)    │ Tunnel │  vLLM Server     │
│                 │        │  (port 8000)     │
└─────────────────┘        └──────────────────┘
```

## Prerequisites

### Required Access

- CURC Alpine cluster account
- SSH access to `login.rc.colorado.edu`
- GPU compute allocation (Ascent or Peak tier recommended)

### Local Machine Requirements

- Python 3.9 or later
- SSH client (built-in on macOS/Linux, available via WSL/PuTTY on Windows)
- 100+ MB free disk space for client dependencies

### CURC Cluster Requirements

- Python 3.10 module
- CUDA 12.1 module
- ~5 GB virtual environment storage
- Model storage space (varies by model, 15-800 GB)

## Quick Start

Follow these steps to get up and running in under 30 minutes.

### Step 1: Clone the Repository

On your local machine:

```bash
git clone <repository-url>
cd curc-LLM-hoster
```

### Step 2: Set Up CURC Environment

SSH into CURC:

```bash
ssh your_username@login.rc.colorado.edu
```

Navigate to your project directory and set up the environment:

```bash
cd /path/to/curc-LLM-hoster
./scripts/setup_environment.sh
```

This will take 10-15 minutes to install vLLM and dependencies.

### Step 3: Launch vLLM Server

Submit a Slurm job to start the server:

```bash
sbatch scripts/launch_vllm.slurm
```

Check job status:

```bash
squeue -u $USER
```

Note your job ID (e.g., 123456).

View the connection information:

```bash
cat logs/connection-info-123456.txt
```

### Step 4: Create SSH Tunnel

On your local machine, create an SSH tunnel:

```bash
./scripts/create_tunnel.sh 123456
```

Replace `123456` with your actual job ID. Leave this terminal open while using the server.

### Step 5: Install Local Dependencies

In a new terminal on your local machine:

```bash
cd curc-LLM-hoster
pip install -r requirements.txt
```

Or install just the client dependencies:

```bash
pip install openai httpx python-dotenv
```

### Step 6: Test the Connection

Run the basic chat example:

```bash
python examples/basic_chat.py
```

If successful, you'll see a response from the LLM.

### Step 7: Interactive Chat

Try the interactive chat interface:

```bash
python examples/interactive_chat.py
```

Type messages and get responses in real-time. Use `/quit` to exit.

## Detailed Setup

### CURC Environment Setup

#### Module Loading

The setup script automatically loads required modules:

```bash
module load python/3.10
module load cuda/12.1
```

To manually load these in your `.bashrc`:

```bash
echo "module load python/3.10" >> ~/.bashrc
echo "module load cuda/12.1" >> ~/.bashrc
```

#### Virtual Environment

The virtual environment is created at `vllm-env/` in your project directory:

```bash
source vllm-env/bin/activate
```

To verify installation:

```bash
python -c "import vllm; print(vllm.__version__)"
```

#### Hugging Face Authentication

For gated models (Llama, etc.), set up your Hugging Face token:

```bash
export HF_TOKEN="your_token_here"
```

Add to your job script or `.bashrc` for persistence.

### Slurm Job Configuration

#### Basic Job Submission

The default configuration requests:
- 1 node
- 1 GPU (A100)
- 8 hour time limit

```bash
sbatch scripts/launch_vllm.slurm
```

#### Custom Configuration

Override defaults with environment variables:

```bash
# Use a different model
MODEL_NAME="meta-llama/Llama-3.1-70B-Instruct" \
TENSOR_PARALLEL_SIZE=4 \
sbatch --gres=gpu:4 scripts/launch_vllm.slurm
```

#### Job Monitoring

Check job status:

```bash
squeue -u $USER
```

View job output in real-time:

```bash
tail -f logs/vllm-server-<job_id>.out
```

Cancel a job:

```bash
scancel <job_id>
```

### SSH Tunnel Setup

#### Automatic Tunnel (Recommended)

Use the provided script:

```bash
./scripts/create_tunnel.sh <job_id>
```

This automatically:
1. Queries Slurm for the compute node
2. Creates the SSH tunnel
3. Displays connection information

#### Manual Tunnel

If you prefer manual control:

```bash
ssh -N -L 8000:c3cpu-a4-u7-4:8000 username@login.rc.colorado.edu
```

Replace `c3cpu-a4-u7-4` with your actual compute node.

#### Tunnel Troubleshooting

If the tunnel fails:

1. Verify the job is running: `squeue -u $USER`
2. Check the compute node name in job output
3. Test SSH connection: `ssh username@login.rc.colorado.edu`
4. Try a different local port: `LOCAL_PORT=9000 ./scripts/create_tunnel.sh <job_id>`

## Usage Examples

### Python Client SDK

#### Basic Chat

```python
from src.client.curc_llm_client import CURCLLMClient

client = CURCLLMClient(base_url="http://localhost:8000")

response = client.chat(
    message="Explain quantum computing in simple terms.",
    temperature=0.7,
    max_tokens=256
)

print(response)
```

#### Streaming Responses

```python
for chunk in client.chat_stream("Write a short poem about science"):
    print(chunk, end="", flush=True)
```

#### With System Prompt

```python
response = client.chat(
    message="What is the capital of France?",
    system_prompt="You are a geography expert. Be concise.",
    temperature=0.3,
    max_tokens=50
)
```

#### Custom Model

```python
response = client.chat(
    message="Hello!",
    model="meta-llama/Llama-3.1-70B-Instruct",
    temperature=0.8
)
```

### Direct OpenAI Client

Use the OpenAI Python library directly:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # Unless you set one
)

response = client.chat.completions.create(
    model="default",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### cURL Examples

Test the API with cURL:

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/v1/models

# Chat completion
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## Configuration

### Server Configuration

Edit `config/server_config.yaml` to customize server settings.

#### Available Presets

- `default`: Small models (7B-13B), 1 GPU
- `medium`: Medium models (30B-34B), 2 GPUs
- `large`: Large models (70B), 4 GPUs
- `xlarge`: Very large models (405B), 8+ GPUs
- `batch`: Optimized for high throughput
- `interactive`: Optimized for low latency

#### Custom Configuration

Create a custom configuration:

```yaml
custom:
  model: "mistralai/Mixtral-8x7B-Instruct-v0.1"
  tensor_parallel_size: 2
  max_model_len: 8192
  gpu_memory_utilization: 0.85
```

### Environment Variables

Create a `.env` file from the example:

```bash
cp config/.env.example .env
```

Edit `.env` with your settings:

```bash
CURC_USER=your_username
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
HF_TOKEN=your_hf_token
```

Load environment variables:

```bash
source .env  # Or use python-dotenv
```

### API Key Authentication

To enable API key authentication:

1. Set an API key:

```bash
export API_KEY="your-secret-key"
```

2. Launch server with authentication:

```bash
API_KEY="your-secret-key" sbatch scripts/launch_vllm.slurm
```

3. Use the key in client requests:

```python
client = CURCLLMClient(
    base_url="http://localhost:8000",
    api_key="your-secret-key"
)
```

## Troubleshooting

### Common Issues

#### "Could not connect to server"

**Symptoms**: Client can't reach the server

**Solutions**:
1. Verify job is running: `squeue -u $USER`
2. Check SSH tunnel is active
3. Verify local port: `lsof -i :8000`
4. Test server health: `curl http://localhost:8000/health`

#### "Out of Memory (OOM)"

**Symptoms**: Job fails with CUDA OOM error

**Solutions**:
1. Reduce `max_model_len`: `MAX_MODEL_LEN=2048`
2. Lower `gpu_memory_utilization`: `GPU_MEMORY_UTILIZATION=0.8`
3. Increase tensor parallelism: Request more GPUs
4. Use quantized model (if available)

#### "Job Pending"

**Symptoms**: Job stays in queue (PD state)

**Solutions**:
1. Check allocation limits: `mybalance`
2. Request shorter time: `--time=04:00:00`
3. Try different partition: `--partition=ami100`
4. Check QoS limits: Contact CURC support

#### "Model Download Fails"

**Symptoms**: Can't download model from Hugging Face

**Solutions**:
1. Set HF token: `export HF_TOKEN="your_token"`
2. Pre-download model to shared storage
3. Use CURC's pre-installed models: `$CURC_LLM_DIR`
4. Check network access from compute nodes

#### "Slow Performance"

**Symptoms**: Low tokens/second throughput

**Solutions**:
1. Check GPU utilization: Should be >80%
2. Increase batch size: `MAX_NUM_BATCHED_TOKENS=8192`
3. Verify tensor parallelism is correct for model size
4. Monitor with: `nvidia-smi` in job output

### Debugging

#### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
sbatch scripts/launch_vllm.slurm
```

#### Check Job Logs

```bash
# Standard output
cat logs/vllm-server-<job_id>.out

# Error output
cat logs/vllm-server-<job_id>.err

# Connection info
cat logs/connection-info-<job_id>.txt
```

#### Test Server Locally on CURC

SSH to the compute node:

```bash
ssh c3cpu-a4-u7-4  # Replace with your node
curl http://localhost:8000/health
```

## Advanced Topics

### Multi-Node Deployment

For very large models (405B+), use multiple nodes:

1. Modify Slurm script:

```bash
#SBATCH --nodes=2
#SBATCH --ntasks=2
#SBATCH --gres=gpu:4
```

2. Set parallelism:

```bash
TENSOR_PARALLEL_SIZE=8 \
PIPELINE_PARALLEL_SIZE=2 \
sbatch scripts/launch_vllm.slurm
```

### Batch Processing

For processing many prompts efficiently:

```python
from src.client.curc_llm_client import CURCLLMClient

client = CURCLLMClient()

prompts = [
    "Summarize: <long text 1>",
    "Summarize: <long text 2>",
    # ... more prompts
]

results = []
for prompt in prompts:
    response = client.complete(prompt, max_tokens=128)
    results.append(response)
```

### Custom Model Loading

To use a custom or fine-tuned model:

1. Upload model to CURC storage
2. Set model path:

```bash
MODEL_NAME="/path/to/your/model" sbatch scripts/launch_vllm.slurm
```

### Performance Benchmarking

Run benchmarks to optimize configuration:

```python
import time
from src.client.curc_llm_client import CURCLLMClient

client = CURCLLMClient()

# Measure latency
start = time.time()
response = client.chat("Hello", max_tokens=100)
latency = time.time() - start

print(f"Latency: {latency:.2f}s")
print(f"Tokens: {len(response.split())}")
print(f"TPS: {len(response.split()) / latency:.2f}")
```

### Integration with Existing Codebases

The OpenAI-compatible API allows drop-in replacement:

```python
# Before: Using OpenAI
# client = OpenAI(api_key="sk-...")

# After: Using CURC LLM
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

# Rest of code unchanged!
```

## Getting Help

### Resources

- CURC Documentation: https://curc.readthedocs.io/
- vLLM Documentation: https://docs.vllm.ai/
- Project Issues: <repository-url>/issues

### Support Channels

- CURC Help: rc-help@colorado.edu
- Project Author: Patrick Cooper

### Reporting Issues

When reporting issues, include:

1. Job ID and Slurm output
2. Error messages from logs
3. Configuration used (model, GPUs, etc.)
4. Steps to reproduce
5. Expected vs actual behavior
