# CURC LLM Hoster - Troubleshooting Guide

Author: Patrick Cooper

This guide provides systematic troubleshooting steps for common issues.

## Diagnostic Checklist

Before troubleshooting, run this diagnostic checklist:

### On CURC

```bash
# 1. Check job status
squeue -u $USER

# 2. Check allocation balance
mybalance

# 3. View job output
tail -20 logs/vllm-server-<job_id>.out

# 4. Check for errors
tail -20 logs/vllm-server-<job_id>.err

# 5. Verify virtual environment
ls -la vllm-env/

# 6. Test Python imports
source vllm-env/bin/activate
python -c "import vllm; print(vllm.__version__)"
```

### On Local Machine

```bash
# 1. Check SSH tunnel
lsof -i :8000

# 2. Test local connection
curl http://localhost:8000/health

# 3. Verify Python dependencies
python -c "import openai; print(openai.__version__)"

# 4. Check network connectivity to CURC
ping login.rc.colorado.edu

# 5. Test SSH access
ssh your_username@login.rc.colorado.edu echo "Connected"
```

## Issue: Environment Setup Fails

### Symptom
`setup_environment.sh` exits with errors

### Diagnostic Steps

1. Check module availability:
```bash
module avail python
module avail cuda
```

2. Verify disk space:
```bash
df -h $HOME
```

3. Check Python version:
```bash
module load python/3.10
python --version
```

### Solutions

**Problem: Insufficient disk space**
- Clean old files: `rm -rf ~/.cache/pip`
- Use scratch space: `cd /scratch/alpine/$USER`

**Problem: Module not found**
- Update module name: `module load python/3.11` (if 3.10 unavailable)
- Contact CURC: rc-help@colorado.edu

**Problem: pip install fails**
- Update pip: `pip install --upgrade pip`
- Use timeout: `pip install --timeout=120 vllm`
- Install dependencies separately

**Problem: CUDA mismatch**
- Load matching CUDA: `module load cuda/12.1`
- Check GPU driver: `nvidia-smi`

## Issue: Slurm Job Fails to Start

### Symptom
Job stays in `PD` (pending) state indefinitely

### Diagnostic Steps

1. Check queue details:
```bash
squeue -u $USER -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
```

2. View detailed job info:
```bash
scontrol show job <job_id>
```

3. Check allocation:
```bash
mybalance
```

### Solutions

**Problem: Insufficient allocation**
- Request less time: Reduce `--time` in Slurm script
- Wait for allocation reset (monthly)
- Apply for higher tier allocation

**Problem: No available GPUs**
- Wait for resources to free up
- Try different partition: `--partition=ami100`
- Use smaller GPU request: `--gres=gpu:1`

**Problem: QoS limits exceeded**
- Check limits: `sacctmgr show qos normal format=name,maxwall,maxsubmit`
- Reduce job count
- Contact CURC support

**Problem: Invalid partition**
- List partitions: `scontrol show partition`
- Use valid partition name
- Check partition access

## Issue: Job Runs But Fails

### Symptom
Job starts but exits with error code

### Diagnostic Steps

1. View error log:
```bash
cat logs/vllm-server-<job_id>.err
```

2. Check exit code:
```bash
sacct -j <job_id> --format=JobID,State,ExitCode
```

3. Review full output:
```bash
cat logs/vllm-server-<job_id>.out
```

### Solutions

**Problem: Out of Memory (OOM)**

Error: `CUDA out of memory` or `RuntimeError: CUDA error`

Solutions:
- Reduce max sequence length: `MAX_MODEL_LEN=2048`
- Lower GPU utilization: `GPU_MEMORY_UTILIZATION=0.7`
- Use smaller model
- Increase tensor parallelism (more GPUs)
- Enable quantization

Example:
```bash
MAX_MODEL_LEN=2048 \
GPU_MEMORY_UTILIZATION=0.8 \
sbatch scripts/launch_vllm.slurm
```

**Problem: Model Download Fails**

Error: `OSError: ... not found` or `ConnectionError`

Solutions:
- Set Hugging Face token: `export HF_TOKEN="your_token"`
- Pre-download model to shared storage
- Use CURC cached models: `MODEL_NAME=$CURC_LLM_DIR/Llama-3.1-8B-Instruct`
- Check network from compute node: SSH to node, test `curl https://huggingface.co`

**Problem: Module Not Found**

Error: `ModuleNotFoundError: No module named 'vllm'`

Solutions:
- Verify virtual environment activation in job script
- Check venv path: `source /full/path/to/vllm-env/bin/activate`
- Reinstall: `./scripts/setup_environment.sh`

**Problem: CUDA Driver Mismatch**

Error: `CUDA driver version is insufficient`

Solutions:
- Load correct CUDA module: `module load cuda/12.1`
- Match CUDA to GPU driver
- Reinstall PyTorch with correct CUDA version

## Issue: Cannot Create SSH Tunnel

### Symptom
`create_tunnel.sh` fails or tunnel disconnects

### Diagnostic Steps

1. Test SSH connection:
```bash
ssh your_username@login.rc.colorado.edu
```

2. Manually create tunnel:
```bash
ssh -N -L 8000:c3cpu-a4-u7-4:8000 your_username@login.rc.colorado.edu
```

3. Check local port availability:
```bash
lsof -i :8000
```

### Solutions

**Problem: Port already in use**

Error: `bind: Address already in use`

Solutions:
- Use different local port: `LOCAL_PORT=9000 ./scripts/create_tunnel.sh`
- Kill existing process: `lsof -ti:8000 | xargs kill`
- Close other tunnels/servers on port 8000

**Problem: Authentication fails**

Error: `Permission denied (publickey,password)`

Solutions:
- Enter correct password
- Set up SSH keys: `ssh-copy-id your_username@login.rc.colorado.edu`
- Check SSH config: `~/.ssh/config`
- Verify username: `CURC_USER=your_username`

**Problem: Cannot reach compute node**

Error: `channel 0: open failed: connect failed`

Solutions:
- Verify job is running: `squeue -u $USER`
- Check correct node name in connection info
- Wait for job to fully start (1-2 minutes after `R` state)
- Ensure firewall allows SSH forwarding

**Problem: Tunnel disconnects**

Solutions:
- Keep terminal open and active
- Use `screen` or `tmux` for persistent sessions
- Add keepalive: `ssh -o ServerAliveInterval=60 ...`
- Check network stability

## Issue: Client Cannot Connect

### Symptom
Python client or curl fails to connect to server

### Diagnostic Steps

1. Test health endpoint:
```bash
curl http://localhost:8000/health
```

2. Check tunnel status:
```bash
lsof -i :8000
```

3. Test from CURC login node:
```bash
ssh your_username@login.rc.colorado.edu
curl http://c3cpu-a4-u7-4:8000/health  # Replace with your compute node
```

### Solutions

**Problem: Connection refused**

Error: `curl: (7) Failed to connect to localhost port 8000`

Solutions:
- Verify SSH tunnel is active
- Recreate tunnel: `./scripts/create_tunnel.sh <job_id>`
- Check job is running: `squeue -u $USER`
- Verify vLLM server started (check logs)

**Problem: Timeout**

Error: `ReadTimeout` or `Connection timeout`

Solutions:
- Increase client timeout: `client = CURCLLMClient(timeout=120)`
- Wait for model to load (first request can take 30+ seconds)
- Check server logs for startup progress
- Verify GPU is accessible

**Problem: 404 Not Found**

Error: `404 Client Error: Not Found`

Solutions:
- Check endpoint URL: Use `/v1/chat/completions` not `/chat/completions`
- Verify base URL: `http://localhost:8000` not `http://localhost:8000/v1`
- Review API documentation: `http://localhost:8000/docs`

**Problem: 401 Unauthorized**

Error: `401 Client Error: Unauthorized`

Solutions:
- Add API key: `client = CURCLLMClient(api_key="your-key")`
- Match key with server: Check `API_KEY` environment variable
- Disable authentication if not needed

## Issue: Slow Performance

### Symptom
Throughput is much lower than expected

### Diagnostic Steps

1. Check GPU utilization:
```bash
# On compute node
nvidia-smi dmon -s u
```

2. Monitor vLLM metrics:
```bash
curl http://localhost:8000/metrics
```

3. Review server logs for warnings:
```bash
grep -i "warning\|slow" logs/vllm-server-<job_id>.out
```

### Solutions

**Problem: Low GPU utilization (<50%)**

Solutions:
- Increase batch size: `MAX_NUM_BATCHED_TOKENS=8192`
- Send more concurrent requests
- Reduce `max_model_len` if not needed
- Check for CPU bottlenecks

**Problem: High latency**

Solutions:
- Use smaller model for faster inference
- Reduce `temperature` for faster sampling
- Lower `max_tokens` in requests
- Check network latency (tunnel overhead)

**Problem: Memory thrashing**

Solutions:
- Reduce `max_num_seqs`
- Lower `gpu_memory_utilization`
- Use quantized model
- Increase tensor parallelism

**Problem: Suboptimal batching**

Solutions:
- Send requests in bursts
- Adjust `max_num_batched_tokens`
- Review continuous batching configuration
- Use async client for concurrent requests

## Issue: Model Quality Problems

### Symptom
Model generates poor or nonsensical responses

### Diagnostic Steps

1. Test with simple prompt:
```python
response = client.chat("Say 'Hello, world!'")
```

2. Check model loading:
```bash
grep "Loading model" logs/vllm-server-<job_id>.out
```

3. Verify model parameters:
```bash
curl http://localhost:8000/v1/models
```

### Solutions

**Problem: Incorrect model loaded**

Solutions:
- Verify `MODEL_NAME` environment variable
- Check model path in logs
- Ensure model is compatible with vLLM
- Use correct model from Hugging Face Hub

**Problem: Poor quality output**

Solutions:
- Adjust temperature (0.7-0.9 for creative, 0.1-0.3 for factual)
- Tune `top_p` and `top_k` parameters
- Provide better system prompts
- Try different model (larger size often = better quality)

**Problem: Truncated responses**

Solutions:
- Increase `max_tokens` in request
- Raise `max_model_len` in server config
- Check for context length limits
- Review stopping criteria

**Problem: Repetitive text**

Solutions:
- Lower `temperature`
- Increase `frequency_penalty`
- Adjust `presence_penalty`
- Use different sampling strategy

## Issue: Cleanup and Restart

### When to Restart

- Server unresponsive
- Performance degraded
- Configuration changes needed
- Testing different models

### Clean Restart Procedure

1. Cancel running job:
```bash
scancel <job_id>
```

2. Close SSH tunnel:
Press `Ctrl+C` in tunnel terminal

3. Clean old logs:
```bash
rm logs/vllm-server-*.out logs/vllm-server-*.err
```

4. Start fresh job:
```bash
sbatch scripts/launch_vllm.slurm
```

5. Recreate tunnel:
```bash
./scripts/create_tunnel.sh <new_job_id>
```

## Getting Additional Help

### Self-Help Resources

1. Check logs first: 90% of issues evident in logs
2. Review documentation: USER_GUIDE.md, TECHNICAL_SPECIFICATION.md
3. Test incrementally: Isolate the failing component

### CURC Support

For cluster-specific issues:
- Email: rc-help@colorado.edu
- Include: Job ID, error logs, steps to reproduce
- Documentation: https://curc.readthedocs.io/

### vLLM Community

For vLLM-specific issues:
- GitHub Issues: https://github.com/vllm-project/vllm/issues
- Documentation: https://docs.vllm.ai/
- Discord: vLLM community server

### Project Issues

For issues with this codebase:
- GitHub: <repository-url>/issues
- Include: Full error messages, configuration, environment details

## Prevention Tips

1. **Test small first**: Start with 8B model before scaling
2. **Monitor resources**: Check GPU memory and allocation regularly
3. **Version control configs**: Track changes to configurations
4. **Document customizations**: Note what worked for your use case
5. **Keep logs**: Archive successful job logs for reference
6. **Regular updates**: Update vLLM and dependencies periodically
7. **Backup configs**: Save working configurations
8. **Read release notes**: Check for breaking changes before updating
