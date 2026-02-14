# CURC Alpine Cluster Setup Guide

Author: Patrick Cooper

This guide provides detailed information about setting up the vLLM environment on CURC's Alpine cluster using conda.

## Overview

The CURC Alpine cluster uses a module system for software management. This project uses conda (via the Anaconda module) to create isolated Python environments for vLLM deployment.

## Why Conda on CURC?

1. **Storage Management**: Conda automatically configures environments to use `/projects/$USER` instead of home directory, avoiding quota issues
2. **Package Management**: Better dependency resolution for complex packages like vLLM and PyTorch
3. **Version Control**: Easy environment versioning and reproducibility
4. **Module Integration**: Works seamlessly with CURC's module system
5. **Recommended by CURC**: Official CURC documentation recommends conda for Python workflows

## System Architecture

### Storage Locations

CURC automatically configures conda to use:
- **Packages**: `/projects/$USER/.conda/pkgs/`
- **Environments**: `/projects/$USER/.conda/envs/`
- **Configuration**: `~/.condarc`

This configuration is automatically created when you first load the anaconda module.

### Module System

CURC uses LMOD for environment modules:
- **Anaconda**: Python distribution with conda package manager
- **CUDA**: GPU compute toolkit for vLLM inference

## Login Nodes vs Compute Nodes

**CRITICAL**: Heavy computation must NOT be done on login nodes.

### Login Nodes
- Hostname pattern: `login-ci*`, `login*`
- Purpose: Job submission, file management, light editing
- **DO NOT**: Compile code, install large packages, run computations

### Compile Nodes
- Access via: `acompile` command
- Purpose: Environment setup, compilation, package installation
- Recommended for: Running `setup_environment.sh`

### Compute Nodes
- Access via: SLURM jobs (`sbatch`, `srun`)
- Purpose: Running vLLM server, GPU workloads
- Automatic: SLURM scripts handle activation

## Step-by-Step Setup

### 1. Initial Login

```bash
ssh your_username@login.rc.colorado.edu
cd /path/to/curc-hoster
```

You'll be on a login node. Verify with:
```bash
hostname  # Should show "login-ci*"
```

### 2. Access Compile Node

Get onto a compile node for environment setup:

```bash
acompile
```

This allocates a compile node for your session. You'll see:
```
Requesting an interactive compile-node session for 24 hours.
Please wait...
```

After allocation, verify you're on a compute node:
```bash
hostname  # Should NOT start with "login"
```

### 3. Run Setup Script

The setup script handles all environment creation:

```bash
./scripts/setup_environment.sh
```

This script will:
1. Warn if you're on a login node (and ask to continue or exit)
2. Load anaconda and CUDA modules
3. Create conda environment named `vllm-env` with Python 3.10
4. Install PyTorch with CUDA 12.1 support
5. Install vLLM inference engine
6. Install Ray for distributed computing
7. Install all dependencies from requirements.txt
8. Verify all installations

Expected output:
```
============================================
CURC vLLM Environment Setup
============================================

Loading required modules...
Anaconda loaded: /curc/sw/anaconda3/2023.09/bin/conda
Python version: Python 3.10.13
CUDA version: release 12.1

Creating conda environment 'vllm-env' with Python 3.10...
...
Setup Complete!
```

Installation takes 10-15 minutes depending on network speed.

### 4. Exit Compile Node

After setup completes:

```bash
exit
```

You'll return to the login node.

### 5. Verify Installation

Load modules and activate environment:

```bash
module load anaconda
conda activate vllm-env
```

Test imports:

```bash
python -c "import vllm; print(f'vLLM version: {vllm.__version__}')"
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

Deactivate when done testing:

```bash
conda deactivate
```

## SLURM Integration

The SLURM job scripts automatically handle environment activation.

### Single-Node Job (launch_vllm.slurm)

```bash
# Load modules
module purge
module load anaconda
module load cuda/12.1

# Initialize conda for bash
eval "$(conda shell.bash hook)"

# Activate environment
conda activate vllm-env

# Run vLLM server
python -m vllm.entrypoints.openai.api_server ...
```

### Multi-Node Job (launch_vllm_multinode.slurm)

Same activation process, but conda environment is shared across all nodes via `/projects/$USER/`.

## Managing Conda Environments

### List Environments

```bash
module load anaconda
conda env list
```

### Activate Environment

```bash
module load anaconda
conda activate vllm-env
```

### Deactivate Environment

```bash
conda deactivate
```

### Remove Environment

If you need to start fresh:

```bash
conda env remove -n vllm-env
```

Then re-run `./scripts/setup_environment.sh`.

### Update Environment

To update packages:

```bash
module load anaconda
conda activate vllm-env
pip install --upgrade vllm
```

## Storage and Quotas

### Check Quota

```bash
# Home directory quota
curc-quota

# Projects directory quota
df -h /projects/$USER
```

### Storage Best Practices

1. **Use `/projects/$USER`**: Conda automatically does this
2. **Clean cache regularly**:
   ```bash
   conda clean --all
   rm -rf ~/.cache/pip
   ```
3. **Remove old environments**: Delete unused conda environments
4. **Monitor usage**: Run `curc-quota` periodically

### Typical Storage Usage

- Base conda environment: ~1 GB
- vLLM + PyTorch + CUDA support: ~5 GB
- Downloaded models: 5-200 GB (depending on model size)

## Module Versions

### Current Configuration (2026)

```bash
module load anaconda      # anaconda/2023.09
module load cuda/12.1     # cuda/12.1.0
```

### Check Available Versions

```bash
module avail anaconda
module avail cuda
```

### Specifying Versions

If needed, specify exact versions:

```bash
module load anaconda/2023.09
module load cuda/12.1.0
```

## Troubleshooting

### Issue: "module: command not found"

**Cause**: Shell not configured for modules

**Solution**: Source the module initialization:
```bash
source /curc/sw/lmod/lmod/init/bash
```

### Issue: Conda environment in home directory

**Cause**: `.condarc` not configured

**Solution**: Check and update `~/.condarc`:
```yaml
envs_dirs:
  - /projects/$USER/.conda/envs
pkgs_dirs:
  - /projects/$USER/.conda/pkgs
```

### Issue: "conda: command not found"

**Cause**: Anaconda module not loaded

**Solution**:
```bash
module load anaconda
```

### Issue: Environment activation fails in SLURM job

**Cause**: Conda not initialized for bash

**Solution**: Add to SLURM script:
```bash
eval "$(conda shell.bash hook)"
conda activate vllm-env
```

### Issue: CUDA not available in Python

**Cause**: CUDA module not loaded or PyTorch CPU-only version

**Solution**:
1. Load CUDA module: `module load cuda/12.1`
2. Verify installation:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```
3. Reinstall PyTorch with CUDA support if needed

### Issue: Out of disk space

**Cause**: Home or projects directory full

**Solutions**:
```bash
# Clean conda cache
conda clean --all

# Clean pip cache
rm -rf ~/.cache/pip

# Check quotas
curc-quota
df -h /projects/$USER

# Remove old environments
conda env remove -n old-env-name
```

## Advanced Configuration

### Custom Conda Configuration

Edit `~/.condarc`:

```yaml
channels:
  - defaults
  - conda-forge
envs_dirs:
  - /projects/$USER/.conda/envs
pkgs_dirs:
  - /projects/$USER/.conda/pkgs
auto_activate_base: false
```

### Environment Export

Save environment for reproducibility:

```bash
conda activate vllm-env
conda env export > environment.yml
```

Recreate environment:

```bash
conda env create -f environment.yml
```

### Using Mamba (Faster Alternative)

CURC also supports Mamba for faster package resolution:

```bash
module load mamba
mamba create -n vllm-env python=3.10 -y
```

## Best Practices

1. **Always use compile nodes**: Run `acompile` before installing packages
2. **Load modules in order**: anaconda, then CUDA
3. **Check disk usage**: Monitor `/projects/$USER` quota
4. **Clean regularly**: Run `conda clean --all` periodically
5. **Use specific versions**: Specify module versions for reproducibility
6. **Test in interactive job**: Test changes before submitting long jobs
7. **Document environment**: Export environment.yml for reproducibility

## References

### CURC Documentation

- [CURC Python and Anaconda Guide](https://curc.readthedocs.io/en/latest/software/python.html)
- [CURC Module System](https://curc.readthedocs.io/en/latest/compute/modules.html)
- [Alpine Quick Start](https://curc.readthedocs.io/en/latest/clusters/alpine/quick-start.html)

### External Resources

- [Conda Documentation](https://docs.conda.io/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [PyTorch CUDA Installation](https://pytorch.org/get-started/locally/)

## Support

### CURC Support

- Email: rc-help@colorado.edu
- Documentation: https://curc.readthedocs.io/
- Office Hours: Check CURC calendar

### Project Issues

- Repository: https://github.com/PatrickAllenCooper/curc-hoster
- Documentation: See `docs/` directory
