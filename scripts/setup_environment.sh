#!/bin/bash

# CURC vLLM Environment Setup Script
# Author: Patrick Cooper
#
# This script sets up the Python virtual environment and installs
# all required dependencies for running vLLM on CURC Alpine cluster.
#
# Usage:
#   ./scripts/setup_environment.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
VENV_DIR="${PROJECT_ROOT}/vllm-env"

echo "============================================"
echo "CURC vLLM Environment Setup"
echo "============================================"
echo ""

# Load required modules
echo "Loading required modules..."
module purge
module load python/3.10
module load cuda/12.1

echo "Python version: $(python --version)"
echo "CUDA version: $(nvcc --version | grep release)"
echo ""

# Create virtual environment
if [ -d "${VENV_DIR}" ]; then
    echo "Virtual environment already exists at: ${VENV_DIR}"
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf "${VENV_DIR}"
    else
        echo "Keeping existing virtual environment."
        exit 0
    fi
fi

echo "Creating virtual environment..."
python -m venv "${VENV_DIR}"

# Activate virtual environment
echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

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
echo "Virtual environment created at: ${VENV_DIR}"
echo ""
echo "To activate the environment:"
echo "  source ${VENV_DIR}/bin/activate"
echo ""
echo "To launch a vLLM server:"
echo "  sbatch scripts/launch_vllm.slurm"
echo ""
