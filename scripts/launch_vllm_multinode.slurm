#!/bin/bash
#SBATCH --job-name=vllm-multinode
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --time=08:00:00
#SBATCH --partition=aa100
#SBATCH --gres=gpu:4
#SBATCH --qos=normal
#SBATCH --output=logs/vllm-multinode-%j.out
#SBATCH --error=logs/vllm-multinode-%j.err

# CURC Multi-Node vLLM Server Launch Script
# Author: Patrick Cooper
#
# This script launches a distributed vLLM inference server across multiple
# nodes using Ray for orchestration and inter-node communication.
#
# Usage:
#   sbatch scripts/launch_vllm_multinode.slurm
#
# Multi-node configuration:
#   --nodes=N              : Number of compute nodes
#   --gres=gpu:M           : GPUs per node
#   --ntasks-per-node=1    : One task per node (for Ray)
#
# Environment variables:
#   MODEL_NAME             : Model to load (default: Llama-3.1-405B-Instruct)
#   TENSOR_PARALLEL_SIZE   : Tensor parallelism (default: 8)
#   PIPELINE_PARALLEL_SIZE : Pipeline parallelism (default: 2)

set -e

# Configuration
MODEL_NAME="${MODEL_NAME:-meta-llama/Llama-3.1-405B-Instruct}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-8}"
PIPELINE_PARALLEL_SIZE="${PIPELINE_PARALLEL_SIZE:-2}"
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
API_KEY="${API_KEY:-}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.9}"

# Ray configuration
RAY_HEAD_PORT="${RAY_HEAD_PORT:-6379}"
RAY_DASHBOARD_PORT="${RAY_DASHBOARD_PORT:-8265}"

# Directories
WORK_DIR="${SLURM_SUBMIT_DIR}"
LOG_DIR="${WORK_DIR}/logs"
VENV_DIR="${WORK_DIR}/vllm-env"

# Create log directory
mkdir -p "${LOG_DIR}"

# Print job information
echo "============================================"
echo "CURC Multi-Node vLLM Server"
echo "============================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Job Name: ${SLURM_JOB_NAME}"
echo "Nodes: ${SLURM_JOB_NODELIST}"
echo "Number of nodes: ${SLURM_JOB_NUM_NODES}"
echo "GPUs per node: ${SLURM_GPUS_PER_NODE}"
echo "Partition: ${SLURM_JOB_PARTITION}"
echo "Working Directory: ${WORK_DIR}"
echo "Start Time: $(date)"
echo "============================================"
echo ""

# Load required modules
echo "Loading modules..."
module purge
module load python/3.10
module load cuda/12.1

# Activate virtual environment
echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Verify vLLM installation
if ! python -c "import vllm" 2>/dev/null; then
    echo "ERROR: vLLM not found in virtual environment"
    exit 1
fi

# Print configuration
echo ""
echo "============================================"
echo "Multi-Node Configuration"
echo "============================================"
echo "Model: ${MODEL_NAME}"
echo "Tensor Parallel Size: ${TENSOR_PARALLEL_SIZE}"
echo "Pipeline Parallel Size: ${PIPELINE_PARALLEL_SIZE}"
echo "Total GPUs: $((SLURM_JOB_NUM_NODES * ${SLURM_GPUS_PER_NODE:-4}))"
echo "Host: ${HOST}"
echo "Port: ${PORT}"
echo "Max Model Length: ${MAX_MODEL_LEN}"
echo "GPU Memory Utilization: ${GPU_MEMORY_UTILIZATION}"
echo "============================================"
echo ""

# Get list of nodes
NODES=$(scontrol show hostname $SLURM_JOB_NODELIST)
NODES_ARRAY=($NODES)
HEAD_NODE=${NODES_ARRAY[0]}
HEAD_NODE_IP=$(srun --nodes=1 --ntasks=1 -w "$HEAD_NODE" hostname --ip-address | awk '{print $1}')

echo "============================================"
echo "Ray Cluster Configuration"
echo "============================================"
echo "Head Node: ${HEAD_NODE}"
echo "Head Node IP: ${HEAD_NODE_IP}"
echo "Ray Port: ${RAY_HEAD_PORT}"
echo "Dashboard Port: ${RAY_DASHBOARD_PORT}"
echo "Worker Nodes: ${SLURM_JOB_NUM_NODES - 1}"
echo "============================================"
echo ""

# Function to cleanup Ray on exit
cleanup() {
    echo "Cleaning up Ray cluster..."
    ray stop
}
trap cleanup EXIT

# Start Ray head node
echo "Starting Ray head node on ${HEAD_NODE}..."
srun --nodes=1 --ntasks=1 -w "$HEAD_NODE" \
    ray start --head \
    --node-ip-address="$HEAD_NODE_IP" \
    --port=${RAY_HEAD_PORT} \
    --dashboard-host=0.0.0.0 \
    --dashboard-port=${RAY_DASHBOARD_PORT} \
    --num-gpus=${SLURM_GPUS_PER_NODE:-4} \
    --block &

# Wait for head node to be ready
sleep 10

# Start Ray worker nodes
echo ""
echo "Starting Ray worker nodes..."
for ((i=1; i<${SLURM_JOB_NUM_NODES}; i++)); do
    NODE=${NODES_ARRAY[$i]}
    echo "  Starting worker on ${NODE}..."
    
    srun --nodes=1 --ntasks=1 -w "$NODE" \
        ray start \
        --address="${HEAD_NODE_IP}:${RAY_HEAD_PORT}" \
        --num-gpus=${SLURM_GPUS_PER_NODE:-4} \
        --block &
    
    sleep 5
done

# Wait for all workers to connect
echo ""
echo "Waiting for Ray cluster to stabilize..."
sleep 10

# Verify Ray cluster
echo ""
echo "Ray cluster status:"
ray status

# Save connection information
CONNECTION_INFO_FILE="${LOG_DIR}/multinode-connection-info-${SLURM_JOB_ID}.txt"
cat > "${CONNECTION_INFO_FILE}" <<EOF
CURC Multi-Node vLLM Server Connection Information
==================================================
Job ID: ${SLURM_JOB_ID}
Head Node: ${HEAD_NODE}
Head Node IP: ${HEAD_NODE_IP}
Port: ${PORT}
Model: ${MODEL_NAME}
Nodes: ${SLURM_JOB_NUM_NODES}
Total GPUs: $((SLURM_JOB_NUM_NODES * ${SLURM_GPUS_PER_NODE:-4}))
Started: $(date)

Ray Dashboard:
  http://${HEAD_NODE_IP}:${RAY_DASHBOARD_PORT}

SSH Tunnel Command (for vLLM API):
  ssh -L ${PORT}:${HEAD_NODE}:${PORT} ${USER}@login.rc.colorado.edu

SSH Tunnel Command (for Ray Dashboard):
  ssh -L ${RAY_DASHBOARD_PORT}:${HEAD_NODE_IP}:${RAY_DASHBOARD_PORT} ${USER}@login.rc.colorado.edu

Local Access URLs:
  vLLM API: http://localhost:${PORT}
  Ray Dashboard: http://localhost:${RAY_DASHBOARD_PORT}

Configuration:
  Tensor Parallel: ${TENSOR_PARALLEL_SIZE}
  Pipeline Parallel: ${PIPELINE_PARALLEL_SIZE}
EOF

echo ""
echo "Connection information saved to: ${CONNECTION_INFO_FILE}"
echo ""

# Build vLLM command for distributed inference
VLLM_CMD="python -m vllm.entrypoints.openai.api_server"
VLLM_CMD="${VLLM_CMD} --model ${MODEL_NAME}"
VLLM_CMD="${VLLM_CMD} --host ${HOST}"
VLLM_CMD="${VLLM_CMD} --port ${PORT}"
VLLM_CMD="${VLLM_CMD} --tensor-parallel-size ${TENSOR_PARALLEL_SIZE}"
VLLM_CMD="${VLLM_CMD} --pipeline-parallel-size ${PIPELINE_PARALLEL_SIZE}"
VLLM_CMD="${VLLM_CMD} --max-model-len ${MAX_MODEL_LEN}"
VLLM_CMD="${VLLM_CMD} --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION}"

# Add API key if set
if [ -n "${API_KEY}" ]; then
    VLLM_CMD="${VLLM_CMD} --api-key ${API_KEY}"
fi

# Launch vLLM server on head node
echo "============================================"
echo "Launching vLLM Server on Ray Cluster"
echo "============================================"
echo "Command: ${VLLM_CMD}"
echo ""
echo "============================================"
echo "Server Output"
echo "============================================"
echo ""

# Run vLLM on head node with Ray cluster
srun --nodes=1 --ntasks=1 -w "$HEAD_NODE" ${VLLM_CMD}
