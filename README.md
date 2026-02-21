# CURC LLM Hoster

Production-grade Large Language Model inference on University of Colorado Boulder Research Computing (CURC) Alpine cluster, with OpenAI-compatible API access from local machines.

**Author**: Patrick Cooper

---

## Overview

This project deploys vLLM inference servers on CURC's A100 GPU nodes and exposes them through an SSH tunnel as a local OpenAI-compatible API. It includes a Python client SDK, interactive examples, and a full test suite.

**What it enables:**
- Host state-of-the-art open-source LLMs on institutional HPC resources
- Query models from any local machine using the OpenAI API format
- Avoid commercial API costs while maintaining data privacy
- Scale from a single A100 to multi-node tensor-parallel deployments

---

## Requirements

**On CURC:**
- Alpine cluster account with GPU allocation (`aa100` partition)
- `vllm-env` conda environment (created by `scripts/setup_environment.sh`)

**On your local machine:**
- Python 3.9+
- SSH client

---

## Repository Structure

```
curc-hoster/
├── scripts/
│   ├── launch_vllm.slurm           # Single-node SLURM job
│   ├── launch_vllm_multinode.slurm # Multi-node tensor-parallel job
│   ├── setup_environment.sh        # One-time conda environment setup
│   ├── create_tunnel.sh            # SSH tunnel helper
│   └── benchmark_performance.py    # Throughput and latency benchmarking
├── src/client/
│   └── curc_llm_client.py          # Python client SDK
├── examples/
│   ├── basic_chat.py               # Single-turn chat
│   ├── streaming_chat.py           # Streaming response
│   └── interactive_chat.py         # Multi-turn CLI
├── tests/                          # 73 tests, 99% coverage
├── config/
│   ├── server_config.yaml          # vLLM presets (8 configurations)
│   └── .env.example                # Environment variable template
├── requirements.txt
└── test_connection.py              # Quick end-to-end connectivity check
```

---

## CURC Setup (One-Time)

SSH into CURC and get onto a compile node — environment setup cannot run on login nodes:

```bash
ssh paco0228@login.rc.colorado.edu
cd /projects/paco0228/curc-hoster
acompile
./scripts/setup_environment.sh
exit
```

The script creates a `vllm-env` conda environment with vLLM, PyTorch (CUDA), and Ray. This takes 10-15 minutes on first run.

**Storage note:** The conda environment installs into `/projects/paco0228/software/anaconda/envs/vllm-env/`. Model weights download to `/scratch/alpine/paco0228/hf_cache/` (set automatically by the SLURM script). Do not store large files in your home directory or `/projects` directly.

---

## Launching the Server

From the CURC login node, submit a SLURM job:

```bash
cd /projects/paco0228/curc-hoster
sbatch scripts/launch_vllm.slurm
```

Override the model or GPU count at submission time:

```bash
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct-AWQ" \
TENSOR_PARALLEL_SIZE=2 \
sbatch --gres=gpu:2 scripts/launch_vllm.slurm
```

Monitor the job:

```bash
squeue -u paco0228
tail -f logs/vllm-server-<JOBID>.out
```

The server is ready when the log shows:

```
INFO:     Application startup complete.
```

Note the compute node name from `squeue` (e.g., `c3gpu-c2-u9`) — you need it for the tunnel.

---

## SSH Tunnel

Open a new local terminal and keep it running while you use the server:

```bash
ssh -L 8000:<NODE>.rc.int.colorado.edu:8000 paco0228@login.rc.colorado.edu
```

Replace `<NODE>` with the node from `squeue` (e.g., `c3gpu-c2-u9`). Approve the Duo push when prompted.

The server is now accessible at `http://localhost:8000`.

---

## Local Client

### Install dependencies

```bash
pip install -r requirements.txt
```

### Verify the connection

```bash
python test_connection.py
```

Expected output:

```
1. Testing health endpoint...
   ✓ Health check: HTTP 200 (ok)

2. Testing models endpoint...
   ✓ Available models: 1
     - Qwen/Qwen2.5-7B-Instruct-AWQ

SUCCESS! Server is ready to use.
```

### Run the examples

```bash
python examples/basic_chat.py        # Single question, printed response
python examples/streaming_chat.py    # Streaming token output
python examples/interactive_chat.py  # Multi-turn CLI (/quit to exit)
```

### Use the SDK directly

```python
from src.client.curc_llm_client import CURCLLMClient

client = CURCLLMClient(base_url="http://localhost:8000")

# Single-turn chat
response = client.chat("Explain quantum entanglement.")
print(response)

# Streaming
for chunk in client.chat_stream("Write a haiku about high-performance computing."):
    print(chunk, end="", flush=True)

# With system prompt
response = client.chat(
    "Summarize this paper abstract: ...",
    system_prompt="You are a research assistant. Be concise.",
    temperature=0.3,
    max_tokens=256,
)
```

The client auto-discovers the loaded model name from `/v1/models` — no need to hard-code it.

---

## Model Selection

The default model is `Qwen/Qwen2.5-7B-Instruct-AWQ`, which fits in a single A100 with 60% memory utilization. Change it by setting `MODEL_NAME` at job submission.

| Model | VRAM | Context | Notes |
|---|---|---|---|
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | ~8 GB | 128K | Default. Fast, fits easily. |
| `Qwen/Qwen2.5-32B-Instruct-AWQ` | ~16 GB | 128K | Better quality, single GPU. |
| `Qwen/Qwen2.5-72B-Instruct-AWQ` | ~36 GB | 128K | Top quality, single A100 80GB. |
| `hugging-quants/Meta-Llama-3.3-70B-Instruct-AWQ-INT4` | ~35 GB | 128K | Strong on coding tasks. |

For models larger than 80 GB, use `launch_vllm_multinode.slurm` with multiple GPUs and `TENSOR_PARALLEL_SIZE` matching the GPU count.

---

## Storage Guidelines

| Path | Purpose | Limit |
|---|---|---|
| `/projects/paco0228/` | Code, configs, small outputs | 250 GB quota |
| `/scratch/alpine/paco0228/` | HF model cache, job outputs, temp data | Purged after 90 days |
| `~` (home) | Config files only | 2 GB quota — do not store models here |

The SLURM script sets `HF_HOME=/scratch/alpine/paco0228/hf_cache` automatically. Models download once and are reused on subsequent jobs.

---

## Configuration

`config/server_config.yaml` contains eight pre-built vLLM server profiles. Copy relevant settings into the SLURM script or pass them as environment variables:

```bash
MAX_MODEL_LEN=8192 GPU_MEMORY_UTILIZATION=0.85 sbatch scripts/launch_vllm.slurm
```

Key variables accepted by `launch_vllm.slurm`:

| Variable | Default | Description |
|---|---|---|
| `MODEL_NAME` | `Qwen/Qwen2.5-7B-Instruct-AWQ` | HuggingFace model ID |
| `TENSOR_PARALLEL_SIZE` | `1` | Number of GPUs for tensor parallelism |
| `PORT` | `8000` | Server port |
| `MAX_MODEL_LEN` | `4096` | Maximum sequence length |
| `GPU_MEMORY_UTILIZATION` | `0.6` | Fraction of GPU VRAM to use |
| `API_KEY` | *(none)* | Optional bearer token for API auth |

---

## Multi-Node Deployment

For models that exceed a single A100's memory (e.g., 405B parameter models):

```bash
TENSOR_PARALLEL_SIZE=8 sbatch --nodes=2 --gres=gpu:4 scripts/launch_vllm_multinode.slurm
```

The multinode script launches a Ray cluster across the allocated nodes automatically.

---

## Testing

```bash
python -m pytest tests/ -v
```

With coverage:

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

**Current status:** 73 tests passing, 99% coverage across:
- Client SDK (chat, streaming, completions, health, model listing)
- Parameter validation and edge cases
- Error handling and concurrency
- Infrastructure and configuration validation
- Performance benchmarking utilities

---

## Troubleshooting

**`Connection refused` on `test_connection.py`**
The SSH tunnel is not established. Make sure the tunnel terminal is open and the node name matches what `squeue` shows.

**`WinError 10054` (connection forcibly closed)**
The vLLM server is still loading the model. Wait for `Application startup complete` in the job log, then retry.

**Server takes 15+ minutes to start**
The model is downloading from HuggingFace. This only happens on first use per model. Subsequent starts load from `/scratch/alpine/paco0228/hf_cache/` in 1-2 minutes.

**`The model 'default' does not exist`**
An outdated version of the client is being used. Pull the latest code: `git pull`.

**SLURM job stuck in `PD` (pending)**
GPU nodes are busy. Check wait time with `sinfo -p aa100`. Try `atesting` partition for short debug sessions (`--time=00:30:00`).

**Out of disk space**
Clear the HuggingFace cache on scratch: `rm -rf /scratch/alpine/paco0228/hf_cache/hub/<model>`. Clear conda caches: `conda clean --all`.

**`module: command not found` in SLURM log**
The SLURM script uses `module load anaconda`. If this fails, check `module avail anaconda` on a login node and update the module name in the script.

---

## Performance

Benchmarked on a single NVIDIA A100 80GB with `Qwen/Qwen2.5-7B-Instruct-AWQ`:

- Throughput: ~793 tokens/second
- Time to first token: <100ms (P99)
- KV cache: 319,296 tokens available (17 GB)
- Max concurrency: ~78 simultaneous requests at 4,096 tokens each

Run the benchmark suite:

```bash
python scripts/benchmark_performance.py --url http://localhost:8000
```

---

## License

MIT License. See `LICENSE` for details.

## References

- [CURC Documentation](https://curc.readthedocs.io)
- [vLLM Documentation](https://docs.vllm.ai)
- [Kwon et al. (2023), "Efficient Memory Management for LLM Serving with PagedAttention"](https://arxiv.org/abs/2309.06180)
