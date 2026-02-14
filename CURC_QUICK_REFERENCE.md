# CURC Conda Setup - Quick Reference

Author: Patrick Cooper

## One-Time Setup

```bash
# 1. SSH to CURC
ssh your_username@login.rc.colorado.edu

# 2. Clone repository
git clone https://github.com/PatrickAllenCooper/curc-hoster.git
cd curc-hoster

# 3. Get onto compile node (REQUIRED - heavy work cannot be on login nodes)
acompile

# 4. Run setup
./scripts/setup_environment.sh

# 5. Exit compile node
exit
```

## Launching vLLM Server

```bash
# From login node - submit job
sbatch scripts/launch_vllm.slurm

# Check job status
squeue -u $USER

# View connection info (replace 123456 with your job ID)
cat logs/connection-info-123456.txt
```

## SSH Tunnel (Local Machine)

```bash
# Create tunnel (replace 123456 with job ID)
./scripts/create_tunnel.sh 123456

# Keep terminal open while using server
```

## Using the Server (Local Machine)

```bash
# Test connection
curl http://localhost:8000/health

# Interactive chat
python examples/interactive_chat.py

# Basic example
python examples/basic_chat.py
```

## Manual Environment Activation (if needed)

```bash
# On CURC (after acompile or in SLURM job)
module load anaconda
conda activate vllm-env

# Deactivate
conda deactivate
```

## Common Commands

```bash
# Check conda environments
module load anaconda
conda env list

# Check disk usage
curc-quota
df -h /projects/$USER

# Clean conda cache
conda clean --all

# View job logs
tail -f logs/vllm-server-<job_id>.out

# Cancel job
scancel <job_id>
```

## Important Notes

1. **Always use `acompile` before setup** - Login nodes cannot handle heavy installation
2. **SLURM scripts auto-activate** - No manual activation needed in jobs
3. **Conda uses `/projects/$USER`** - Avoids home directory quota issues
4. **Keep tunnel open** - SSH tunnel must stay active while querying server

## Troubleshooting Quick Fixes

```bash
# Module not found
module avail anaconda
module load anaconda/2023.09

# Environment not found
conda env list
# If missing, re-run setup_environment.sh

# Out of space
conda clean --all
rm -rf ~/.cache/pip

# Job pending too long
mybalance  # Check allocation
# Try shorter time in SLURM script
```

## File Locations

- **Setup script**: `scripts/setup_environment.sh`
- **SLURM job**: `scripts/launch_vllm.slurm`
- **Multi-node**: `scripts/launch_vllm_multinode.slurm`
- **Logs**: `logs/vllm-server-<job_id>.out`
- **Connection info**: `logs/connection-info-<job_id>.txt`
- **Conda env**: `/projects/$USER/.conda/envs/vllm-env/`

## Full Documentation

- `QUICKSTART.md` - 15-minute getting started guide
- `docs/CURC_SETUP.md` - Comprehensive conda setup guide
- `docs/TROUBLESHOOTING.md` - Detailed problem solving
- `CONDA_MIGRATION.md` - Migration details and rationale
- `README.md` - Project overview
