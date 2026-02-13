# CURC LLM Hoster - Quick Start Guide

Author: Patrick Cooper

**Get up and running with LLM hosting on CURC in 15 minutes**

## What You'll Accomplish

By the end of this guide, you'll have:
1. A vLLM inference server running on CURC Alpine cluster
2. An SSH tunnel connecting your local machine to the server
3. An interactive chat interface to query the LLM

## Prerequisites

- CURC Alpine cluster account
- SSH access to CURC
- Python 3.9+ on your local machine
- 30 minutes of GPU time in your allocation

## Step-by-Step Instructions

### 1. On CURC: Clone and Setup (10 minutes)

SSH into CURC:

```bash
ssh your_username@login.rc.colorado.edu
```

Clone the repository:

```bash
cd ~  # or your preferred directory
git clone <repository-url> curc-LLM-hoster
cd curc-LLM-hoster
```

Run the environment setup:

```bash
./scripts/setup_environment.sh
```

This will:
- Load Python 3.10 and CUDA 12.1 modules
- Create a virtual environment
- Install vLLM, Ray, PyTorch, and dependencies
- Verify the installation

Expected time: 10-15 minutes

### 2. On CURC: Launch Server (2 minutes)

Create logs directory:

```bash
mkdir -p logs
```

Submit the Slurm job.

**For best performance** (Qwen 2.5 72B - top ranked open source model):

```bash
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct-AWQ" sbatch scripts/launch_vllm.slurm
```

**Or use the default** (Llama 3.1 8B - smaller, faster):

```bash
sbatch scripts/launch_vllm.slurm
```

**Other high-end options** for single A100 80GB:
```bash
# Llama 3.3 70B (excellent for coding)
MODEL_NAME="hugging-quants/Meta-Llama-3.3-70B-Instruct-AWQ-INT4" sbatch scripts/launch_vllm.slurm

# Qwen 2.5 32B (fastest, 128K context)
MODEL_NAME="Qwen/Qwen2.5-32B-Instruct-AWQ" sbatch scripts/launch_vllm.slurm
```

See `docs/MODEL_GUIDE.md` for complete model selection guidance.

You'll see output like:
```
Submitted batch job 123456
```

**Save this job ID!** You'll need it for the SSH tunnel.

Check job status:

```bash
squeue -u $USER
```

Wait until the job state changes from `PD` (pending) to `R` (running). This usually takes 1-5 minutes.

View the connection information:

```bash
cat logs/connection-info-123456.txt  # Replace with your job ID
```

You'll see the compute node name and port number.

### 3. On Local Machine: Install Client (2 minutes)

Open a terminal on your local machine.

Clone the repository (if not already done):

```bash
cd ~  # or your preferred directory
git clone <repository-url> curc-LLM-hoster
cd curc-LLM-hoster
```

Install dependencies:

```bash
pip install openai httpx python-dotenv
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 4. On Local Machine: Create SSH Tunnel (1 minute)

Create the SSH tunnel using your job ID:

```bash
./scripts/create_tunnel.sh 123456  # Replace with your job ID
```

When prompted, enter your CURC password.

You'll see:

```
SSH tunnel command:
  ssh -N -L 8000:c3cpu-a4-u7-4:8000 your_username@login.rc.colorado.edu

After tunnel is established:
  Server URL: http://localhost:8000
  API Docs: http://localhost:8000/docs
  Health Check: http://localhost:8000/health

Press Ctrl+C to close the tunnel.
```

**Keep this terminal open!** The tunnel must remain active to query the server.

### 5. On Local Machine: Test Connection (30 seconds)

Open a **new terminal** (keep the tunnel terminal running).

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

You should see:

```json
{"status": "ok"}
```

Or similar health status.

### 6. On Local Machine: Chat with the LLM (Instant)

Run the interactive chat:

```bash
cd curc-LLM-hoster
python examples/interactive_chat.py
```

You'll see:

```
CURC LLM Interactive Chat
==================================================

Server Status: {'status': 'ok'}
Available models: 1
  - meta-llama/Llama-3.1-8B-Instruct

Commands:
  /quit or /exit - Exit the chat
  /clear - Clear conversation history
  /help - Show this help message

==================================================

You: 
```

Type a message:

```
You: Explain quantum computing in simple terms.
```

The LLM will respond with a streaming answer.

Type `/quit` to exit.

## Quick Test Script

Alternatively, test with the basic chat example:

```bash
python examples/basic_chat.py
```

Or with Python directly:

```python
from src.client.curc_llm_client import CURCLLMClient

client = CURCLLMClient(base_url="http://localhost:8000")

# Simple chat
response = client.chat("Hello, how are you?")
print(response)

# Streaming chat
for chunk in client.chat_stream("Write a haiku about science"):
    print(chunk, end="", flush=True)
```

## Verify Everything Works

### Checklist

- [ ] Virtual environment created on CURC
- [ ] vLLM server job running on CURC (check with `squeue`)
- [ ] SSH tunnel active on local machine
- [ ] Health check returns OK (`curl http://localhost:8000/health`)
- [ ] Interactive chat responds to messages

### Expected Performance

For Llama 3.1 8B on single A100 GPU:
- First response: 2-5 seconds (model loading)
- Subsequent responses: <1 second to first token
- Throughput: 100-500 tokens/second

## Common Issues

### "Could not connect to server"

**Problem**: Client can't reach vLLM server

**Solutions**:
1. Check job is running: `squeue -u $USER` (on CURC)
2. Verify SSH tunnel is active (keep terminal open)
3. Check local port: `lsof -i :8000`
4. Test health: `curl http://localhost:8000/health`

### "Job pending (PD)"

**Problem**: Slurm job not starting

**Solutions**:
1. Wait 5-10 minutes (jobs queue during busy times)
2. Check allocation: `mybalance` (on CURC)
3. Try shorter time: Edit `scripts/launch_vllm.slurm`, change `--time=04:00:00`

### "Module not found"

**Problem**: Python can't find client module

**Solutions**:
1. Ensure you're in project directory: `cd curc-LLM-hoster`
2. Install dependencies: `pip install openai httpx`
3. Verify Python version: `python --version` (need 3.9+)

## Next Steps

### Try Different Models

Edit the Slurm script to use a different model:

```bash
MODEL_NAME="meta-llama/Llama-3.1-70B-Instruct" \
TENSOR_PARALLEL_SIZE=4 \
sbatch --gres=gpu:4 scripts/launch_vllm.slurm
```

### Customize Configuration

Edit `config/server_config.yaml` for performance tuning.

### Read Full Documentation

- `Guidance_Documents/USER_GUIDE.md` - Complete user guide
- `Guidance_Documents/TECHNICAL_SPECIFICATION.md` - Architecture details
- `examples/` - More code examples

## Cleanup

When done, clean up resources:

1. Cancel Slurm job (on CURC):

```bash
scancel 123456  # Replace with your job ID
```

2. Close SSH tunnel (on local machine):

Press `Ctrl+C` in the tunnel terminal.

3. Logout from CURC:

```bash
exit
```

## Getting Help

If you encounter issues:

1. Check `logs/vllm-server-<job_id>.out` on CURC
2. Review the troubleshooting section in `USER_GUIDE.md`
3. Contact CURC support: rc-help@colorado.edu

## Summary

You've successfully:
- Deployed a production-grade LLM inference server on CURC
- Created secure SSH tunnel for local access
- Queried the LLM using OpenAI-compatible API
- Learned the complete workflow from deployment to usage

The same workflow scales to larger models and multi-GPU setups!
