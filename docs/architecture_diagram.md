# CURC LLM Hoster - Architecture Diagram

Author: Patrick Cooper

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Local Machine (User)                                │
│                                                                             │
│  ┌──────────────────┐         ┌─────────────────────────────────────────┐  │
│  │                  │         │     Python Applications                  │  │
│  │  SSH Tunnel      │         │                                         │  │
│  │  (Port 8000)     │◄────────┤  - Interactive Chat                     │  │
│  │                  │         │  - Streaming Examples                   │  │
│  │  create_tunnel.sh│         │  - Custom Scripts                       │  │
│  └─────────┬────────┘         │  - OpenAI Client SDK                    │  │
│            │                  └───────────────┬─────────────────────────┘  │
└────────────┼──────────────────────────────────┼────────────────────────────┘
             │                                  │
             │ SSH Encrypted Tunnel             │ HTTP API Calls
             │ (login.rc.colorado.edu)          │ (localhost:8000)
             │                                  │
             ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CURC Alpine HPC Cluster                                │
│                                                                             │
│  ┌─────────────────┐           ┌──────────────────────────────────────┐    │
│  │  Login Node     │           │       Compute Node                   │    │
│  │                 │           │  (Allocated via Slurm)               │    │
│  │  - SSH Gateway  │           │                                      │    │
│  │  - Slurm Submit │◄──────────┤  ┌────────────────────────────────┐  │    │
│  │  - File System  │           │  │   vLLM Server Process          │  │    │
│  └─────────────────┘           │  │   (launch_vllm.slurm)          │  │    │
│                                │  │                                │  │    │
│  ┌─────────────────┐           │  │  - OpenAI API (:8000)         │  │    │
│  │  Setup Scripts  │           │  │  - Model Loading              │  │    │
│  │                 │           │  │  - PagedAttention             │  │    │
│  │  setup_env.sh ──┼───────┐   │  │  - Batch Inference            │  │    │
│  └─────────────────┘       │   │  │  - Health Monitoring          │  │    │
│                            │   │  └────────────┬───────────────────┘  │    │
│  ┌─────────────────┐       │   │               │                      │    │
│  │  Virtual Env    │◄──────┘   │               ▼                      │    │
│  │  vllm-env/      │           │  ┌────────────────────────────────┐  │    │
│  │                 │           │  │   GPU Resources                │  │    │
│  │  - vLLM         │           │  │   (NVIDIA A100 / L40 / MI100)  │  │    │
│  │  - Ray          │           │  │                                │  │    │
│  │  - PyTorch      │           │  │  - Tensor Cores                │  │    │
│  │  - Dependencies │           │  │  - CUDA Memory (80 GB)         │  │    │
│  └─────────────────┘           │  │  - KV Cache                    │  │    │
│                                │  └────────────────────────────────┘  │    │
│  ┌─────────────────┐           │                                      │    │
│  │  Shared Storage │           │  ┌────────────────────────────────┐  │    │
│  │                 │           │  │   Logs & Outputs               │  │    │
│  │  - Models       │───────────┼─►│                                │  │    │
│  │  - Logs         │           │  │  - vllm-server-*.out           │  │    │
│  │  - Configs      │           │  │  - connection-info-*.txt       │  │    │
│  └─────────────────┘           │  └────────────────────────────────┘  │    │
│                                └──────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Deployment Workflow

```
┌──────────────┐
│ User Action  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Setup Environment on CURC                                 │
│    ./scripts/setup_environment.sh                            │
│    - Load modules (Python, CUDA)                             │
│    - Create virtual environment                              │
│    - Install vLLM, Ray, PyTorch                              │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Submit Slurm Job                                          │
│    sbatch scripts/launch_vllm.slurm                          │
│    - Allocate GPU resources                                  │
│    - Start vLLM server                                       │
│    - Generate connection info                                │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Create SSH Tunnel (Local Machine)                         │
│    ./scripts/create_tunnel.sh <JOB_ID>                       │
│    - Query Slurm for compute node                            │
│    - Establish SSH port forwarding                           │
│    - Map localhost:8000 → compute_node:8000                  │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Query LLM (Local Machine)                                 │
│    python examples/interactive_chat.py                       │
│    - Send HTTP requests to localhost:8000                    │
│    - Tunnel forwards to vLLM server                          │
│    - Receive responses                                       │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Query → Python Client → SSH Tunnel → CURC Login → Compute Node → vLLM
    ↑                                                                    ↓
    └────────────────────────── Response ────────────────────────────────┘
```

### Detailed Request Flow

1. **User sends query** via Python client (`CURCLLMClient`)
2. **HTTP request** to `http://localhost:8000/v1/chat/completions`
3. **SSH tunnel** forwards to `compute_node:8000`
4. **vLLM server** receives request
5. **Model inference** on GPU with PagedAttention
6. **Response generation** (streaming or complete)
7. **SSH tunnel** forwards response back
8. **Client receives** and displays result

## Component Interactions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURC Compute Node                               │
│                                                                         │
│  ┌────────────────┐      ┌────────────────┐      ┌──────────────────┐  │
│  │                │      │                │      │                  │  │
│  │  HTTP Server   │◄────►│  vLLM Engine   │◄────►│  GPU (A100)      │  │
│  │  (FastAPI)     │      │                │      │                  │  │
│  │                │      │  - Scheduler   │      │  - Model Weights │  │
│  │  Port 8000     │      │  - Executor    │      │  - KV Cache      │  │
│  │                │      │  - Memory Mgr  │      │  - Computation   │  │
│  └────────┬───────┘      └────────┬───────┘      └──────────────────┘  │
│           │                       │                                    │
│           ▼                       ▼                                    │
│  ┌────────────────────────────────────────────┐                       │
│  │           Request Queue                     │                       │
│  │  - Continuous Batching                      │                       │
│  │  - Priority Scheduling                      │                       │
│  │  - Dynamic Memory Allocation                │                       │
│  └────────────────────────────────────────────┘                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Security Layers                                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 1: CURC Network Isolation                                   │  │
│  │ - Compute nodes not directly accessible from internet             │  │
│  │ - Login node acts as bastion host                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 2: SSH Encryption                                           │  │
│  │ - All traffic encrypted via SSH tunnel                            │  │
│  │ - User authentication required                                    │  │
│  │ - Key-based or password authentication                            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 3: API Key Authentication (Optional)                        │  │
│  │ - Bearer token for API requests                                   │  │
│  │ - Configurable per deployment                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 4: Slurm Resource Isolation                                 │  │
│  │ - Jobs run with user credentials                                  │  │
│  │ - Resource limits enforced                                        │  │
│  │ - Allocation-based access control                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Scalability Architecture

### Single-Node (Current Implementation)

```
┌────────────────────────────────────────┐
│         Compute Node                   │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  vLLM Server                     │  │
│  │  - Model: Llama 3.1 8B          │  │
│  │  - GPUs: 1x A100                │  │
│  │  - Throughput: 500+ TPS         │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

### Multi-GPU (Tensor Parallelism)

```
┌────────────────────────────────────────┐
│         Compute Node                   │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  vLLM Server                     │  │
│  │  - Model: Llama 3.1 70B         │  │
│  │  - GPUs: 4x A100                │  │
│  │  - Tensor Parallel: 4           │  │
│  │  - Throughput: 400+ TPS         │  │
│  └──────────────────────────────────┘  │
│                                        │
│  GPU 0  │  GPU 1  │  GPU 2  │  GPU 3  │
│  [Model Slice 1] [Slice 2] [Slice 3]  │
│  [Slice 4]                             │
└────────────────────────────────────────┘
```

### Multi-Node (Future)

```
┌─────────────────────┐       ┌─────────────────────┐
│   Head Node         │       │   Worker Node       │
│                     │       │                     │
│  ┌──────────────┐   │       │  ┌──────────────┐   │
│  │  Ray Head    │◄──┼───────┼─►│  Ray Worker  │   │
│  │  vLLM Server │   │       │  │  vLLM Engine │   │
│  └──────────────┘   │       │  └──────────────┘   │
│                     │       │                     │
│  GPU 0-3            │       │  GPU 0-3            │
└─────────────────────┘       └─────────────────────┘

Model: Llama 3.1 405B
Total GPUs: 8 (4 per node)
Tensor Parallel: 8
Pipeline Parallel: 2
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│  - Python Client SDK (OpenAI-compatible)                        │
│  - Interactive Examples                                         │
│  - Custom User Scripts                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                    API Layer                                    │
│  - vLLM OpenAI Server (FastAPI)                                 │
│  - REST API (chat, completions, models, health)                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                    Inference Engine                             │
│  - vLLM Core (PagedAttention, Continuous Batching)              │
│  - Ray (Multi-node Orchestration)                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                    ML Framework                                 │
│  - PyTorch                                                      │
│  - CUDA / cuDNN                                                 │
│  - Transformers Library                                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                    Infrastructure                               │
│  - Slurm Workload Manager                                       │
│  - CURC Alpine Cluster                                          │
│  - NVIDIA GPUs (A100, L40, MI100)                               │
└─────────────────────────────────────────────────────────────────┘
```
