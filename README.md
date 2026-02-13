# CURC LLM Hoster

Production-grade Large Language Model inference infrastructure for University of Colorado Boulder Research Computing resources.

**Author**: Patrick Cooper

---

## Overview

This project provides a complete deployment solution for hosting and serving Large Language Models on CURC's Alpine HPC cluster. Built on vLLM and Ray, it enables efficient multi-GPU and multi-node inference with OpenAI-compatible API endpoints.

For quick deployment, see the [Quick Start Guide](QUICKSTART.md).

## Key Features

- **High Performance**: Greater than 500 tokens/second throughput on single A100 GPU
- **Scalable**: Multi-GPU and multi-node distributed inference via Ray
- **Memory Efficient**: PagedAttention reduces memory waste by 60-80%
- **API Compatible**: OpenAI-compatible REST API for easy integration
- **Production Ready**: Supports concurrent multi-user workloads (10-100 users)
- **CURC Optimized**: Native Slurm integration with Alpine cluster allocation management
- **Comprehensive Testing**: 71 tests with 100% code coverage
- **Well Documented**: Complete guides for deployment, usage, and troubleshooting

## Quick Start

### Prerequisites

- CURC Alpine cluster access with GPU allocation
- Python 3.9+ (both on CURC and local machine)
- SSH access to `login.rc.colorado.edu`
- Hugging Face account (for gated model downloads)

### Step 1: Setup on CURC

SSH to CURC and run the setup script:

```bash
ssh your_username@login.rc.colorado.edu
cd /path/to/curc-LLM-hoster
./scripts/setup_environment.sh
```

### Step 2: Launch vLLM Server

Submit a Slurm job:

```bash
sbatch scripts/launch_vllm.slurm
```

Check job status and note the job ID:

```bash
squeue -u $USER
# Note your job ID (e.g., 123456)
```

### Step 3: Create SSH Tunnel

On your local machine:

```bash
./scripts/create_tunnel.sh 123456  # Replace with your job ID
```

Keep this terminal open while using the server.

### Step 4: Install Local Client

On your local machine:

```bash
pip install -r requirements.txt
```

### Step 5: Query the LLM

Run the interactive chat:

```bash
python examples/interactive_chat.py
```

Or use the Python client:

```python
from src.client.curc_llm_client import CURCLLMClient

client = CURCLLMClient(base_url="http://localhost:8000")
response = client.chat("Explain quantum computing in simple terms.")
print(response)
```

For detailed instructions, see the [User Guide](Guidance_Documents/USER_GUIDE.md).

## Project Structure

```
curc-LLM-hoster/
├── README.md                           # Project overview
├── paper.tex                           # Project goals and objectives
├── requirements.txt                    # Python dependencies
├── setup.py                            # Package installation
├── pytest.ini                          # Test configuration
├── Guidance_Documents/                 # Technical documentation
│   ├── TECHNICAL_SPECIFICATION.md      # Architecture and design
│   └── USER_GUIDE.md                   # End-user documentation
├── scripts/                            # Deployment automation
│   ├── setup_environment.sh            # CURC environment setup
│   ├── launch_vllm.slurm               # Single-node Slurm job
│   ├── launch_vllm_multinode.slurm     # Multi-node deployment
│   ├── create_tunnel.sh                # SSH tunnel automation
│   └── benchmark_performance.py        # Performance benchmarking
├── src/                                # Source code
│   └── client/                         # Client SDK
│       ├── __init__.py
│       └── curc_llm_client.py          # OpenAI-compatible client
├── examples/                           # Usage examples
│   ├── basic_chat.py                   # Simple chat example
│   ├── streaming_chat.py               # Streaming responses
│   └── interactive_chat.py             # Interactive CLI
├── config/                             # Configuration files
│   ├── server_config.yaml              # vLLM server configs (8 presets)
│   └── .env.example                    # Environment template
├── tests/                              # Test suite (100% coverage)
│   ├── __init__.py
│   ├── test_client.py                  # Client tests
│   ├── test_validation.py              # Validation & edge cases
│   ├── test_examples.py                # Infrastructure tests
│   └── test_benchmark.py               # Benchmark tests
├── docs/                               # Additional documentation
│   ├── MODEL_GUIDE.md                  # Model selection guide
│   ├── BENCHMARKING.md                 # Performance benchmarking
│   ├── MULTI_NODE.md                   # Multi-node deployment
│   ├── TROUBLESHOOTING.md              # Problem solving
│   └── architecture_diagram.md         # System diagrams
└── logs/                               # Runtime logs (auto-created)
```

## Architecture

The system deploys vLLM inference servers across CURC Alpine cluster nodes, orchestrated by Ray for distributed inference:

- **Frontend**: OpenAI-compatible REST API
- **Backend**: vLLM inference engine with PagedAttention
- **Orchestration**: Ray cluster for multi-node coordination
- **Scheduling**: Slurm job submission and resource management

See `Guidance_Documents/TECHNICAL_SPECIFICATION.md` for detailed architecture.

## Supported Models

The infrastructure supports any Hugging Face model compatible with vLLM.

### Recommended High-End Models for Single A100 80GB (AWQ Quantized)

Based on February 2026 open source LLM rankings:

**Qwen 2.5 72B AWQ** (Recommended)
- Top ranked open source model as of February 2026
- Memory: ~36 GB VRAM, 128K context window
- License: Apache 2.0
- Model ID: `Qwen/Qwen2.5-72B-Instruct-AWQ`

**Llama 3.3 70B AWQ**
- Excellent performance on coding tasks
- Memory: ~35 GB VRAM
- Model ID: `hugging-quants/Meta-Llama-3.3-70B-Instruct-AWQ-INT4`

**Llama 3.1 70B AWQ**
- Proven stability and wide adoption
- Memory: ~35 GB VRAM
- Model ID: `hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4`

**Qwen 2.5 32B AWQ** (Fastest)
- 2-3x faster inference than 70B models
- Memory: ~16 GB VRAM, 128K context window
- Model ID: `Qwen/Qwen2.5-32B-Instruct-AWQ`

For detailed model selection guidance, see `docs/MODEL_GUIDE.md`.

### Also Supported

- Llama 3.1 (8B, 70B, 405B) - FP16 multi-GPU
- Mistral/Mixtral series
- Gemma series
- DeepSeek models
- And many more from Hugging Face

## Performance Characteristics

Benchmarked on NVIDIA A100 (80GB) with vLLM:

- **Throughput**: 793 tokens/second (single GPU, unquantized models)
- **Latency**: P99 less than 100ms for interactive queries
- **Concurrency**: Supports 10-100 simultaneous users
- **Memory Efficiency**: 60-80% reduction in KV cache fragmentation vs naive implementation
- **Scalability**: Linear scaling with multi-GPU tensor parallelism

For performance benchmarking tools, see `scripts/benchmark_performance.py` and `docs/BENCHMARKING.md`.

## Documentation

### Core Documentation

- **paper.tex**: Project goals and success criteria
- **QUICKSTART.md**: 15-minute deployment guide
- **Guidance_Documents/TECHNICAL_SPECIFICATION.md**: Architecture and design
- **Guidance_Documents/USER_GUIDE.md**: Complete user guide
- **docs/MODEL_GUIDE.md**: Model selection guidance
- **docs/BENCHMARKING.md**: Performance testing guide
- **docs/MULTI_NODE.md**: Multi-node deployment guide
- **docs/TROUBLESHOOTING.md**: Systematic problem solving

### Example Code

- `examples/basic_chat.py`: Simple synchronous chat
- `examples/streaming_chat.py`: Streaming response demonstration
- `examples/interactive_chat.py`: Full-featured CLI interface

### External References

- [CURC LLM Documentation](https://curc.readthedocs.io/en/latest/ai-ml/llms.html)
- [vLLM Documentation](https://docs.vllm.ai/)
- [vLLM OpenAI-Compatible Server](https://docs.vllm.ai/en/stable/serving/openai_compatible_server/)
- [PagedAttention Paper](https://arxiv.org/abs/2309.06180)

## Development Status

**All Deliverables Complete**

This project has achieved all objectives specified in paper.tex:

- Research and architecture design
- Technical specification and documentation
- Single-node deployment scripts (Slurm, environment setup)
- Multi-node deployment scripts (Ray cluster orchestration)
- SSH tunnel automation for secure local access
- Python client SDK with 100% test coverage
- Comprehensive test suite (71 unit tests passing)
- Performance benchmarking suite (latency, throughput, concurrency)
- Complete user documentation and working examples
- Configuration management with 8 model presets
- Support for high-end models (Qwen 2.5 72B, Llama 3.3 70B)
- Comprehensive model selection guide

The system is production-ready for immediate deployment on CURC resources.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

With coverage report:

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View detailed report
```

**Test Statistics**:
- 71 unit tests passing
- 100% code coverage (exceeds 90% requirement)
- 4 test suites covering all components
- Comprehensive mocking for offline testing
- Integration tests available (require running server)

**Test Coverage**:
- Core client functionality (22 tests)
- Parameter validation and edge cases (23 tests)
- Infrastructure and documentation validation (20 tests)
- Performance benchmarking (6 tests)
- Error handling and concurrency scenarios
- Unicode, special characters, and extreme values

Complete test documentation available in `tests/TEST_REPORT.md`.

## Project Information

### Author

Patrick Cooper  
University of Colorado Boulder

### Status

This project is complete and production-ready. All deliverables from paper.tex have been implemented and tested.

### License

MIT License. See LICENSE file for details.

### Citation

If you use this work in your research, please cite:

```bibtex
@software{cooper2026curc,
  author = {Cooper, Patrick},
  title = {CURC LLM Hoster: Production-Grade LLM Inference on HPC Resources},
  year = {2026},
  url = {https://github.com/PatrickAllenCooper/curc-hoster}
}
```

### Support

For issues or questions:
- CURC cluster support: rc-help@colorado.edu
- Project repository: https://github.com/PatrickAllenCooper/curc-hoster

### Acknowledgments

This project builds upon the following technologies:
- University of Colorado Boulder Research Computing (CURC) infrastructure
- vLLM inference engine by UC Berkeley
- Ray distributed computing framework
- Hugging Face model ecosystem

## References

### Technical Papers

- Kwon et al. (2023). "Efficient Memory Management for Large Language Model Serving with PagedAttention." arXiv:2309.06180.
- Performance comparison study: "Comparative Analysis of Large Language Model Inference Serving Systems" arXiv:2511.17593.

### Documentation

- [CURC Alpine Documentation](https://curc.readthedocs.io/)
- [vLLM Official Documentation](https://docs.vllm.ai/)
- [Ray Documentation](https://docs.ray.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
