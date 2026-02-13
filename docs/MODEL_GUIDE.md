# CURC LLM Hoster - Model Selection Guide

Author: Patrick Cooper

Last Updated: 2026-02-13

## Overview

This guide helps you select the optimal open source LLM for your use case and available GPU resources on CURC Alpine cluster.

## GPU Resources on CURC Alpine

Available GPU types:
- **NVIDIA A100 (80GB)**: Primary GPU for large model inference
- **NVIDIA L40 (48GB)**: Good for medium models
- **AMD MI100 (32GB)**: Suitable for smaller models

## Recommended Models by GPU Configuration

### Single A100 80GB - Quantized High-End Models (AWQ 4-bit)

These represent the **best open source LLMs** that can run on a single A100 80GB GPU using AWQ 4-bit quantization.

#### 1. Qwen 2.5 72B (AWQ) - **RECOMMENDED**

**Configuration**: `qwen_72b_awq`

**Why Choose This:**
- **Top ranked** open source model as of February 2026
- Best overall performance-to-resource ratio
- 128K context window (configurable)
- Apache 2.0 license (fully commercial use)

**Specifications:**
- Parameters: 72 billion (4-bit quantized)
- VRAM Required: ~36 GB
- Context Length: Up to 128K tokens
- License: Apache 2.0

**Best For:**
- General purpose tasks
- Long context understanding
- Multilingual applications
- Production deployments

**Usage:**
```bash
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct-AWQ" \
sbatch scripts/launch_vllm.slurm
```

Or use the preset:
```bash
# Edit launch script to load qwen_72b_awq config
sbatch scripts/launch_vllm.slurm
```

**Performance:**
- Quality Index: 46+ (February 2026 rankings)
- Excellent on reasoning, coding, and general tasks
- Supports 128K context (start with 8K-16K for best performance)

---

#### 2. Llama 3.3 70B (AWQ)

**Configuration**: `llama_33_70b_awq`

**Why Choose This:**
- Strong general purpose performance
- Excellent coding capabilities
- Large ecosystem and community support
- Meta's latest 70B model

**Specifications:**
- Parameters: 70 billion (4-bit quantized)
- VRAM Required: ~35 GB
- Context Length: 8K tokens (expandable)
- License: Llama 3 Community License

**Best For:**
- Code generation and analysis
- General reasoning tasks
- Users familiar with Llama ecosystem
- Applications requiring proven stability

**Usage:**
```bash
MODEL_NAME="hugging-quants/Meta-Llama-3.3-70B-Instruct-AWQ-INT4" \
sbatch scripts/launch_vllm.slurm
```

**Performance:**
- Strong coding benchmarks
- Competitive reasoning capabilities
- Well-optimized for vLLM

---

#### 3. Llama 3.1 70B (AWQ)

**Configuration**: `llama_31_70b_awq`

**Why Choose This:**
- Proven and battle-tested
- Extensive fine-tuned variants available
- Large community support
- Wide compatibility

**Specifications:**
- Parameters: 70 billion (4-bit quantized)
- VRAM Required: ~35 GB
- Context Length: 8K tokens
- License: Llama 3 Community License

**Best For:**
- When you need proven stability
- Access to many fine-tuned variants
- Compatibility with existing Llama 3.1 tools
- Research applications

**Usage:**
```bash
MODEL_NAME="hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4" \
sbatch scripts/launch_vllm.slurm
```

---

#### 4. Qwen 2.5 32B (AWQ) - **FASTEST**

**Configuration**: `qwen_32b_awq`

**Why Choose This:**
- Smaller model = more headroom for batching
- Very fast inference
- Still highly capable
- 128K context window

**Specifications:**
- Parameters: 32 billion (4-bit quantized)
- VRAM Required: ~16 GB
- Context Length: Up to 128K tokens
- License: Apache 2.0

**Best For:**
- High-throughput batch processing
- Longer context windows (can handle 16K-32K easily)
- Cost-sensitive applications (uses less GPU time)
- When speed is more important than maximum capability

**Usage:**
```bash
MODEL_NAME="Qwen/Qwen2.5-32B-Instruct-AWQ" \
sbatch scripts/launch_vllm.slurm
```

**Performance:**
- 2-3x faster than 70B models
- Can handle 2x the concurrent requests
- Still very capable for most tasks

---

### Multiple A100 GPUs - Unquantized Large Models

For multi-GPU setups, you can run larger models without quantization:

#### Llama 3.1 70B (FP16) - 4x A100

**Configuration**: `large`

- Full precision (no quantization loss)
- Highest quality outputs
- Requires 4x A100 GPUs with tensor parallelism

#### Llama 3.1 405B (FP16) - 8+ A100

**Configuration**: `xlarge`

- State-of-the-art open source model
- Requires 8+ A100 GPUs
- Best for research and highest quality needs

---

## Model Comparison Table

| Model | Params | Quant | VRAM | GPUs | Context | License | Best For |
|-------|--------|-------|------|------|---------|---------|----------|
| **Qwen 2.5 72B AWQ** | 72B | AWQ-4 | ~36GB | 1 | 128K | Apache 2.0 | Overall best, production |
| **Llama 3.3 70B AWQ** | 70B | AWQ-4 | ~35GB | 1 | 8K | Llama 3 | Coding, general purpose |
| **Llama 3.1 70B AWQ** | 70B | AWQ-4 | ~35GB | 1 | 8K | Llama 3 | Stability, proven |
| **Qwen 2.5 32B AWQ** | 32B | AWQ-4 | ~16GB | 1 | 128K | Apache 2.0 | Speed, long context |
| Llama 3.1 70B FP16 | 70B | None | ~140GB | 4 | 8K | Llama 3 | Max quality |
| Llama 3.1 405B FP16 | 405B | None | ~810GB | 10+ | 8K | Llama 3 | Research, SOTA |

---

## Quantization Explained

### AWQ (Activation-aware Weight Quantization)

**Advantages:**
- 4-bit precision (75% VRAM reduction)
- Minimal quality loss (<3% on most benchmarks)
- 3x faster inference than FP16
- Excellent vLLM support

**When to Use:**
- Single GPU deployment
- Need to maximize model size on available VRAM
- Production environments prioritizing cost efficiency

**Performance:**
- ~97% of full precision quality
- Significant speedup on inference

---

## Selection Decision Tree

```
Do you have multiple A100 GPUs?
├─ YES → Use FP16 models (large, xlarge configs)
│         - Better quality
│         - No quantization loss
│
└─ NO (Single A100) → Use AWQ models
    │
    ├─ Need absolute best performance?
    │  └─ Use Qwen 2.5 72B AWQ (qwen_72b_awq)
    │
    ├─ Focus on coding tasks?
    │  └─ Use Llama 3.3 70B AWQ (llama_33_70b_awq)
    │
    ├─ Need proven stability?
    │  └─ Use Llama 3.1 70B AWQ (llama_31_70b_awq)
    │
    └─ Need speed or long context?
       └─ Use Qwen 2.5 32B AWQ (qwen_32b_awq)
```

---

## Benchmark Rankings (February 2026)

Based on latest open source LLM rankings:

1. **Qwen 3 72B** - Quality Index 46.77
   - AIME 2025: 96%
   - LiveCodeBench: 85%
   - Best overall open source model

2. **Llama 3.3 70B** - Strong general purpose
   - Competitive with GPT-4 class models
   - Excellent coding performance

3. **Llama 3.1 70B** - Proven baseline
   - Widely adopted
   - Extensive ecosystem

---

## License Considerations

### Apache 2.0 (Qwen Models)
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Patent grant included
- No restrictions on use case

### Llama 3 Community License
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ⚠️ Some restrictions on very large deployments (>700M users)
- Generally permissive for most use cases

---

## Performance Optimization Tips

### For Maximum Throughput (Batch Processing)

Use smaller models with higher batching:
```bash
MODEL_NAME="Qwen/Qwen2.5-32B-Instruct-AWQ" \
MAX_NUM_SEQS=128 \
MAX_NUM_BATCHED_TOKENS=16384 \
sbatch scripts/launch_vllm.slurm
```

### For Minimum Latency (Interactive)

Use optimized settings:
```bash
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct-AWQ" \
MAX_NUM_SEQS=16 \
GPU_MEMORY_UTILIZATION=0.85 \
sbatch scripts/launch_vllm.slurm
```

### For Long Context

Use Qwen models with increased context:
```bash
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct-AWQ" \
MAX_MODEL_LEN=32768 \
GPU_MEMORY_UTILIZATION=0.9 \
sbatch scripts/launch_vllm.slurm
```

---

## Common Use Cases

### Research and Experimentation
**Recommended**: Qwen 2.5 72B AWQ
- Best overall performance
- Flexible licensing
- Good balance of all capabilities

### Production Code Generation
**Recommended**: Llama 3.3 70B AWQ
- Strong coding benchmarks
- Proven in production
- Good ecosystem support

### High-Volume Batch Processing
**Recommended**: Qwen 2.5 32B AWQ
- 2-3x faster
- Can handle more concurrent requests
- Lower cost per token

### Long Document Analysis
**Recommended**: Qwen 2.5 72B or 32B AWQ
- 128K context window
- Excellent for summarization
- Good at information extraction

---

## Getting Started

1. **Choose your model** from the recommendations above
2. **Use the preset** in `config/server_config.yaml`
3. **Launch on CURC**:

```bash
# For Qwen 2.5 72B (recommended)
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct-AWQ" \
sbatch scripts/launch_vllm.slurm

# For Llama 3.3 70B
MODEL_NAME="hugging-quants/Meta-Llama-3.3-70B-Instruct-AWQ-INT4" \
sbatch scripts/launch_vllm.slurm

# For Qwen 2.5 32B (fastest)
MODEL_NAME="Qwen/Qwen2.5-32B-Instruct-AWQ" \
sbatch scripts/launch_vllm.slurm
```

4. **Create SSH tunnel** from local machine
5. **Start querying** via OpenAI-compatible API

---

## Troubleshooting

### Out of Memory with 72B Model

Try these in order:
1. Lower `MAX_MODEL_LEN=4096`
2. Reduce `GPU_MEMORY_UTILIZATION=0.85`
3. Decrease `MAX_NUM_SEQS=16`
4. Use 32B model instead

### Slow Performance

1. Check GPU utilization (should be >80%)
2. Increase batch size for throughput
3. Use 32B model for faster inference
4. Verify quantization is working

### Model Download Issues

```bash
# Set Hugging Face token
export HF_TOKEN="your_token_here"

# Or use CURC cached models
export MODEL_NAME="$CURC_LLM_DIR/model_name"
```

---

## References

- [Qwen 2.5 Documentation](https://qwen.readthedocs.io/)
- [Llama 3.3 Release](https://www.llama.com/)
- [vLLM Quantization Guide](https://docs.vllm.ai/)
- [AWQ Paper](https://arxiv.org/abs/2306.00978)
- [February 2026 LLM Rankings](https://whatllm.org/)

---

## Questions?

For model-specific questions:
- Qwen: https://github.com/QwenLM/Qwen
- Llama: https://github.com/meta-llama
- vLLM: https://github.com/vllm-project/vllm

For CURC deployment help, see:
- `Guidance_Documents/USER_GUIDE.md`
- `docs/TROUBLESHOOTING.md`
