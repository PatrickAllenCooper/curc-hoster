# Conda Migration Summary

Author: Patrick Cooper
Date: 2026-02-14

## Overview

This project has been migrated from using CURC's `python/3.10` module with virtual environments to using the Anaconda module with conda environments. This change aligns with CURC best practices and resolves the module availability issue encountered during setup.

## Why This Change Was Necessary

### Problem
When running `./scripts/setup_environment.sh` on CURC Alpine, the script failed with:

```
Lmod has detected the following error: The following module(s) are unknown: "python/3.10"
```

The `python/3.10` module does not exist on CURC Alpine in 2026.

### Solution
CURC recommends using the Anaconda module for Python environments on Alpine. Anaconda provides:

1. Better package management for complex dependencies
2. Automatic storage configuration (uses `/projects/$USER` instead of home directory)
3. Easier dependency resolution for packages like vLLM and PyTorch
4. Official CURC support and documentation

## What Changed

### 1. Environment Setup Script (`scripts/setup_environment.sh`)

**Before:**
```bash
module load python/3.10
python -m venv vllm-env
source vllm-env/bin/activate
```

**After:**
```bash
module load anaconda
conda create -n vllm-env python=3.10 -y
conda activate vllm-env
```

**Additional Changes:**
- Added login node detection with warning
- Recommends using `acompile` before running setup
- Updated activation instructions

### 2. SLURM Job Scripts

Both `launch_vllm.slurm` and `launch_vllm_multinode.slurm` updated:

**Before:**
```bash
module load python/3.10
source vllm-env/bin/activate
```

**After:**
```bash
module load anaconda
eval "$(conda shell.bash hook)"
conda activate vllm-env
```

### 3. Documentation Updates

**Updated Files:**
- `README.md` - Added `acompile` step and conda notes
- `QUICKSTART.md` - Updated setup instructions with conda workflow
- `PROJECT_SUMMARY.md` - Changed "virtual environment" to "conda environment"
- `docs/TROUBLESHOOTING.md` - Added conda-specific troubleshooting

**New File:**
- `docs/CURC_SETUP.md` - Comprehensive conda setup guide for CURC Alpine

## How to Use the New Setup

### First-Time Setup

1. **SSH to CURC:**
   ```bash
   ssh your_username@login.rc.colorado.edu
   cd /path/to/curc-hoster
   ```

2. **Get onto compile node (IMPORTANT):**
   ```bash
   acompile
   ```

3. **Run setup script:**
   ```bash
   ./scripts/setup_environment.sh
   ```

4. **Exit compile node:**
   ```bash
   exit
   ```

### Launching Jobs

No changes to job submission workflow:

```bash
# From login node
sbatch scripts/launch_vllm.slurm
```

The SLURM scripts automatically handle conda environment activation.

### Manual Environment Activation

If you need to activate the environment manually:

```bash
module load anaconda
conda activate vllm-env
```

Deactivate:

```bash
conda deactivate
```

## Key Differences from Old Setup

| Aspect | Old (venv) | New (conda) |
|--------|-----------|-------------|
| Module | `python/3.10` | `anaconda` |
| Create | `python -m venv vllm-env` | `conda create -n vllm-env` |
| Activate | `source vllm-env/bin/activate` | `conda activate vllm-env` |
| Location | `./vllm-env/` | `/projects/$USER/.conda/envs/vllm-env/` |
| Storage | Project directory | Projects directory (automatic) |
| Login node check | No | Yes (with warning) |

## Benefits of Conda Setup

1. **Better Package Management**: Conda handles complex dependencies more reliably
2. **Storage Optimization**: Automatically uses `/projects/$USER` to avoid home directory quota issues
3. **CURC Supported**: Aligns with official CURC documentation and recommendations
4. **Easier Cleanup**: `conda clean --all` clears caches easily
5. **Environment Export**: Easy to export and reproduce environments

## Compatibility Notes

### What Stays the Same

- All Python code and client libraries
- SLURM job submission commands
- SSH tunnel creation
- API endpoints and usage
- Model configurations
- Documentation structure

### What Changes

- Initial setup procedure (now uses `acompile` + conda)
- Environment activation commands
- Storage location of packages
- Module loading in SLURM scripts

## Troubleshooting

### "Module anaconda not found"

Check available versions:
```bash
module avail anaconda
```

Load specific version:
```bash
module load anaconda/2023.09
```

### "Conda command not found"

Load anaconda module first:
```bash
module load anaconda
```

### "Running on login node" warning

The setup script will warn if you're on a login node. This is intentional:

1. Exit the setup script
2. Run `acompile` to get onto a compute node
3. Re-run the setup script

### Environment in wrong location

Check `~/.condarc`:
```yaml
envs_dirs:
  - /projects/$USER/.conda/envs
pkgs_dirs:
  - /projects/$USER/.conda/pkgs
```

This should be automatically created when you load anaconda for the first time.

## Migration for Existing Users

If you have an existing `vllm-env` virtual environment:

1. **Backup** (optional):
   ```bash
   mv vllm-env vllm-env.backup
   ```

2. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

3. **Get onto compile node:**
   ```bash
   acompile
   ```

4. **Run setup script:**
   ```bash
   ./scripts/setup_environment.sh
   ```

5. **Test:**
   ```bash
   module load anaconda
   conda activate vllm-env
   python -c "import vllm; print(vllm.__version__)"
   ```

6. **Clean up old environment** (after verifying new one works):
   ```bash
   rm -rf vllm-env.backup
   ```

## References

### CURC Documentation

- [Python and Anaconda on Alpine](https://curc.readthedocs.io/en/latest/software/python.html)
- [Module System Documentation](https://curc.readthedocs.io/en/latest/compute/modules.html)
- [Alpine Quick Start](https://curc.readthedocs.io/en/latest/clusters/alpine/quick-start.html)

### Project Documentation

- `docs/CURC_SETUP.md` - Comprehensive conda setup guide
- `QUICKSTART.md` - Updated quick start with conda
- `docs/TROUBLESHOOTING.md` - Conda-specific troubleshooting

## Summary

This migration ensures compatibility with CURC Alpine's current module system and follows CURC best practices. The setup is now more robust, better integrated with CURC infrastructure, and uses storage more efficiently.

All functionality remains the same - only the environment setup and activation methods have changed.
