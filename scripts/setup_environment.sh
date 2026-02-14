#!/bin/bash

# CURC vLLM Environment Setup Script
# Author: Patrick Cooper
#
# This script sets up the conda environment and installs
# all required dependencies for running vLLM on CURC Alpine cluster.
#
# IMPORTANT: This script should be run on a compute node, not a login node.
# From a login node, first run: acompile
# Then execute this script.
#
# Usage:
#   acompile                        # Get onto compute node
#   ./scripts/setup_environment.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
CONDA_ENV_NAME="vllm-env"

echo "============================================"
echo "CURC vLLM Environment Setup"
echo "============================================"
echo ""

# Check if we're on a login node
HOSTNAME=$(hostname)
if [[ $HOSTNAME == login* ]]; then
    echo "WARNING: You appear to be on a login node ($HOSTNAME)"
    echo "Heavy compute should not be done on login nodes."
    echo ""
    echo "Please run 'acompile' first to get onto a compute node,"
    echo "then re-run this script."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please run 'acompile' first."
        exit 1
    fi
fi

# Load required modules
echo "Loading required modules..."
module purge
module load anaconda
module load cuda/12.1

echo "Anaconda loaded: $(which conda)"
echo "Python version: $(python --version)"
echo "CUDA version: $(nvcc --version | grep release)"
echo ""

# Check if conda environment already exists
if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
    echo "Conda environment '${CONDA_ENV_NAME}' already exists."
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing conda environment..."
        conda env remove -n "${CONDA_ENV_NAME}" -y
    else
        echo "Keeping existing conda environment."
        echo "To activate: conda activate ${CONDA_ENV_NAME}"
        exit 0
    fi
fi

echo "Creating conda environment '${CONDA_ENV_NAME}' with Python 3.10..."
conda create -n "${CONDA_ENV_NAME}" python=3.10 -y

# Activate conda environment
echo "Activating conda environment..."
source activate "${CONDA_ENV_NAME}"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA support
echo ""
echo "Installing PyTorch with CUDA 12.1 support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install vLLM
echo ""
echo "Installing vLLM..."
pip install vllm

# Install Ray for distributed inference
echo ""
echo "Installing Ray..."
pip install "ray[default]"

# Install additional dependencies
echo ""
echo "Installing additional dependencies..."
pip install \
    openai \
    httpx \
    python-dotenv \
    pyyaml \
    requests \
    pytest \
    pytest-asyncio \
    pytest-cov

# Install project in development mode
echo ""
echo "Installing project in development mode..."
cd "${PROJECT_ROOT}"
if [ -f "setup.py" ]; then
    pip install -e .
else
    echo "No setup.py found, skipping project installation"
fi

# Verify installations
echo ""
echo "============================================"
echo "Verifying Installation"
echo "============================================"

echo "Python packages:"
pip list | grep -E "(torch|vllm|ray|openai)"

echo ""
echo "Testing vLLM import..."
python -c "import vllm; print(f'vLLM version: {vllm.__version__}')"

echo ""
echo "Testing Ray import..."
python -c "import ray; print(f'Ray version: {ray.__version__}')"

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Conda environment created: ${CONDA_ENV_NAME}"
echo ""
echo "To activate the environment (after loading modules):"
echo "  module load anaconda"
echo "  conda activate ${CONDA_ENV_NAME}"
echo ""
echo "To launch a vLLM server (from login node):"
echo "  sbatch scripts/launch_vllm.slurm"
echo ""
echo "Note: The SLURM job scripts will automatically load"
echo "the conda environment when running on compute nodes."
echo ""
