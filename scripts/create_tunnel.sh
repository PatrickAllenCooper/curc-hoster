#!/bin/bash

# SSH Tunnel Creation Script for CURC vLLM Server
# Author: Patrick Cooper
#
# This script creates an SSH tunnel from your local machine to the
# vLLM server running on a CURC Alpine compute node.
#
# Usage:
#   ./scripts/create_tunnel.sh [JOB_ID]
#
# If JOB_ID is not provided, the script will show active vLLM jobs.

set -e

# Configuration
CURC_LOGIN="login.rc.colorado.edu"
CURC_USER="${CURC_USER:-${USER}}"
LOCAL_PORT="${LOCAL_PORT:-8000}"
REMOTE_PORT="${REMOTE_PORT:-8000}"

# Function to display usage
usage() {
    echo "Usage: $0 [JOB_ID]"
    echo ""
    echo "Creates an SSH tunnel to access vLLM server on CURC Alpine cluster."
    echo ""
    echo "Options:"
    echo "  JOB_ID          Slurm job ID of the running vLLM server"
    echo ""
    echo "Environment Variables:"
    echo "  CURC_USER       CURC username (default: \$USER)"
    echo "  LOCAL_PORT      Local port for tunnel (default: 8000)"
    echo "  REMOTE_PORT     Remote port on compute node (default: 8000)"
    echo ""
    echo "Examples:"
    echo "  $0 12345                     # Connect to job 12345"
    echo "  LOCAL_PORT=9000 $0 12345     # Use local port 9000"
    echo ""
    exit 1
}

# Function to get connection info
get_connection_info() {
    local job_id=$1
    local log_dir="logs"
    local conn_file="${log_dir}/connection-info-${job_id}.txt"
    
    if [ -f "${conn_file}" ]; then
        cat "${conn_file}"
        return 0
    else
        echo "Connection info file not found: ${conn_file}"
        return 1
    fi
}

# Function to extract compute node from Slurm
get_compute_node() {
    local job_id=$1
    
    echo "Querying Slurm for job ${job_id}..." >&2
    
    # SSH to CURC and get node list
    local nodelist=$(ssh "${CURC_USER}@${CURC_LOGIN}" \
        "squeue -j ${job_id} -h -o %N" 2>/dev/null)
    
    if [ -z "${nodelist}" ]; then
        echo "ERROR: Job ${job_id} not found or not running" >&2
        return 1
    fi
    
    echo "${nodelist}"
}

# Main script
main() {
    local job_id=$1
    
    # Check if job ID provided
    if [ -z "${job_id}" ]; then
        echo "ERROR: Job ID required"
        echo ""
        usage
    fi
    
    # Validate job ID is numeric
    if ! [[ "${job_id}" =~ ^[0-9]+$ ]]; then
        echo "ERROR: Job ID must be numeric"
        exit 1
    fi
    
    echo "============================================"
    echo "CURC vLLM SSH Tunnel Setup"
    echo "============================================"
    echo "Job ID: ${job_id}"
    echo "CURC User: ${CURC_USER}"
    echo "Local Port: ${LOCAL_PORT}"
    echo "Remote Port: ${REMOTE_PORT}"
    echo ""
    
    # Get compute node
    echo "Retrieving compute node information..."
    COMPUTE_NODE=$(get_compute_node "${job_id}")
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "Failed to retrieve compute node. Make sure:"
        echo "  1. Job ${job_id} is running"
        echo "  2. You have SSH access to CURC"
        echo "  3. CURC_USER is set correctly"
        exit 1
    fi
    
    echo "Compute Node: ${COMPUTE_NODE}"
    echo ""
    
    # Display connection info if available
    echo "Connection Information:"
    echo "----------------------------------------"
    get_connection_info "${job_id}" 2>/dev/null || echo "No saved connection info found"
    echo ""
    
    # Create SSH tunnel
    echo "============================================"
    echo "Creating SSH Tunnel"
    echo "============================================"
    echo ""
    echo "SSH tunnel command:"
    echo "  ssh -N -L ${LOCAL_PORT}:${COMPUTE_NODE}:${REMOTE_PORT} ${CURC_USER}@${CURC_LOGIN}"
    echo ""
    echo "After tunnel is established:"
    echo "  Server URL: http://localhost:${LOCAL_PORT}"
    echo "  API Docs: http://localhost:${LOCAL_PORT}/docs"
    echo "  Health Check: http://localhost:${LOCAL_PORT}/health"
    echo ""
    echo "Press Ctrl+C to close the tunnel."
    echo "============================================"
    echo ""
    
    # Create the tunnel (this will block)
    ssh -N -L "${LOCAL_PORT}:${COMPUTE_NODE}:${REMOTE_PORT}" \
        "${CURC_USER}@${CURC_LOGIN}"
}

# Handle command line arguments
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    usage
fi

main "$@"
