#!/bin/bash
#SBATCH --job-name=vllm-server
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=08:00:00
#SBATCH --partition=aa100
#SBATCH --gres=gpu:1
#SBATCH --qos=normal
#SBATCH --output=logs/vllm-server-%j.out
#SBATCH --error=logs/vllm-server-%j.err

# CURC vLLM Server Launch Script
# Author: Patrick Cooper
# 
# This script launches a vLLM inference server on CURC Alpine cluster
# with OpenAI-compatible API endpoints.
#
# Usage:
#   sbatch scripts/launch_vllm.slurm
#
# Custom parameters (modify as needed):
#   --nodes=N          : Number of nodes for multi-node deployment
#   --gres=gpu:N       : Number of GPUs per node
#   --time=HH:MM:SS    : Maximum runtime
#   --partition=PART   : Partition (aa100, ami100, etc.)

set -e

# Configuration
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct-AWQ}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
API_KEY="${API_KEY:-}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.9}"

# Directories
WORK_DIR="${SLURM_SUBMIT_DIR}"
LOG_DIR="${WORK_DIR}/logs"
CONDA_ENV_NAME="vllm-env"

# Create log directory
mkdir -p "${LOG_DIR}"

# Print job information
echo "============================================"
echo "CURC vLLM Server Job Information"
echo "============================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Job Name: ${SLURM_JOB_NAME}"
echo "Node(s): ${SLURM_JOB_NODELIST}"
echo "Number of nodes: ${SLURM_JOB_NUM_NODES}"
echo "GPUs per node: ${SLURM_GPUS_PER_NODE:-N/A}"
echo "Partition: ${SLURM_JOB_PARTITION}"
echo "Working Directory: ${WORK_DIR}"
echo "Start Time: $(date)"
echo "============================================"
echo ""

# Load required modules
echo "Loading modules..."
module purge
module load anaconda
module load cuda/12.1

# Initialize conda for bash
eval "$(conda shell.bash hook)"

# Check if conda environment exists
if ! conda env list | grep -q "^${CONDA_ENV_NAME} "; then
    echo "ERROR: Conda environment '${CONDA_ENV_NAME}' not found"
    echo "Please run: scripts/setup_environment.sh"
    echo ""
    echo "Available conda environments:"
    conda env list
    exit 1
fi

# Activate conda environment
echo "Activating conda environment '${CONDA_ENV_NAME}'..."
conda activate "${CONDA_ENV_NAME}"

# Verify vLLM installation
if ! python -c "import vllm" 2>/dev/null; then
    echo "ERROR: vLLM not found in conda environment '${CONDA_ENV_NAME}'"
    echo "Please run: scripts/setup_environment.sh"
    exit 1
fi

# Print configuration
echo ""
echo "============================================"
echo "vLLM Server Configuration"
echo "============================================"
echo "Model: ${MODEL_NAME}"
echo "Tensor Parallel Size: ${TENSOR_PARALLEL_SIZE}"
echo "Host: ${HOST}"
echo "Port: ${PORT}"
echo "Max Model Length: ${MAX_MODEL_LEN}"
echo "GPU Memory Utilization: ${GPU_MEMORY_UTILIZATION}"
echo "API Key: ${API_KEY:+***SET***}"
echo "============================================"
echo ""

# Get node hostname for SSH tunnel information
NODE_HOSTNAME=$(hostname)
echo "============================================"
echo "Connection Information"
echo "============================================"
echo "Server will be accessible at: http://${NODE_HOSTNAME}:${PORT}"
echo ""
echo "To access from your local machine, create an SSH tunnel:"
echo "  ssh -L ${PORT}:${NODE_HOSTNAME}:${PORT} ${USER}@login.rc.colorado.edu"
echo ""
echo "Then access locally at: http://localhost:${PORT}"
echo "============================================"
echo ""

# Save connection info to file for easy retrieval
CONNECTION_INFO_FILE="${LOG_DIR}/connection-info-${SLURM_JOB_ID}.txt"
cat > "${CONNECTION_INFO_FILE}" <<EOF
CURC vLLM Server Connection Information
========================================
Job ID: ${SLURM_JOB_ID}
Node: ${NODE_HOSTNAME}
Port: ${PORT}
Model: ${MODEL_NAME}
Started: $(date)

SSH Tunnel Command:
  ssh -L ${PORT}:${NODE_HOSTNAME}:${PORT} ${USER}@login.rc.colorado.edu

Local Access URL:
  http://localhost:${PORT}

API Key: ${API_KEY:+***SET***}
EOF

echo "Connection information saved to: ${CONNECTION_INFO_FILE}"
echo ""

# Build vLLM command
VLLM_CMD="python -m vllm.entrypoints.openai.api_server"
VLLM_CMD="${VLLM_CMD} --model ${MODEL_NAME}"
VLLM_CMD="${VLLM_CMD} --host ${HOST}"
VLLM_CMD="${VLLM_CMD} --port ${PORT}"
VLLM_CMD="${VLLM_CMD} --tensor-parallel-size ${TENSOR_PARALLEL_SIZE}"
VLLM_CMD="${VLLM_CMD} --max-model-len ${MAX_MODEL_LEN}"
VLLM_CMD="${VLLM_CMD} --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION}"

# Add API key if set
if [ -n "${API_KEY}" ]; then
    VLLM_CMD="${VLLM_CMD} --api-key ${API_KEY}"
fi

# Launch vLLM server
echo "Launching vLLM server..."
echo "Command: ${VLLM_CMD}"
echo ""
echo "============================================"
echo "Server Output"
echo "============================================"
echo ""

# Execute vLLM
exec ${VLLM_CMD}
