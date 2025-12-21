#!/bin/bash

# Period Remove Script
# Periodically checks a folder and removes subfolders older than a specified age

# Default values
CHECK_INTERVAL=30  # seconds between checks
MAX_AGE=5          # seconds - subfolders older than this will be removed
TARGET_DIR=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 -d <directory> [-i <check_interval>] [-a <max_age>]"
    echo "  -d: Target directory to monitor (required)"
    echo "  -i: Check interval in seconds (default: 30)"
    echo "  -a: Maximum age of subfolders in seconds (default: 5)"
    echo "  -h: Display this help message"
    echo ""
    echo "Example: $0 -d /tmp/myfolders -i 60 -a 10"
    exit 1
}

# Function to log messages with timestamp
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)
            echo -e "${timestamp} [${GREEN}INFO${NC}] $message"
            ;;
        WARN)
            echo -e "${timestamp} [${YELLOW}WARN${NC}] $message"
            ;;
        ERROR)
            echo -e "${timestamp} [${RED}ERROR${NC}] $message"
            ;;
    esac
}

# Parse command line arguments
while getopts "d:i:a:h" opt; do
    case $opt in
        d)
            TARGET_DIR="$OPTARG"
            ;;
        i)
            CHECK_INTERVAL="$OPTARG"
            ;;
        a)
            MAX_AGE="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done

# Validate required arguments
if [ -z "$TARGET_DIR" ]; then
    log ERROR "Target directory is required"
    usage
fi

# Create directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    log INFO "Directory does not exist, creating: $TARGET_DIR"
    if mkdir -p "$TARGET_DIR" 2>/dev/null; then
        log INFO "Successfully created directory: $TARGET_DIR"
    else
        log ERROR "Failed to create directory: $TARGET_DIR"
        exit 1
    fi
fi

# Validate numeric arguments
if ! [[ "$CHECK_INTERVAL" =~ ^[0-9]+$ ]]; then
    log ERROR "Check interval must be a positive integer"
    exit 1
fi

if ! [[ "$MAX_AGE" =~ ^[0-9]+$ ]]; then
    log ERROR "Max age must be a positive integer"
    exit 1
fi

# Display configuration
log INFO "Starting periodic cleanup monitor"
log INFO "Target directory: $TARGET_DIR"
log INFO "Check interval: ${CHECK_INTERVAL}s"
log INFO "Max subfolder age: ${MAX_AGE}s"
log INFO "Press Ctrl+C to stop"

# Trap to handle graceful shutdown
trap 'log INFO "Stopping cleanup monitor..."; exit 0' SIGINT SIGTERM

# Main monitoring loop
while true; do
    log INFO "Checking for old subfolders..."
    
    removed_count=0
    checked_count=0
    
    # Get current time in seconds since epoch
    current_time=$(date +%s)
    
    # Check each subfolder in the target directory
    for subfolder in "$TARGET_DIR"/*; do
        # Skip if not a directory
        if [ ! -d "$subfolder" ]; then
            continue
        fi
        
        checked_count=$((checked_count + 1))
        
        # Get the modification time of the subfolder
        # Using stat with different syntax for Linux vs macOS compatibility
        if stat --version &>/dev/null; then
            # GNU stat (Linux)
            folder_mtime=$(stat -c %Y "$subfolder" 2>/dev/null)
        else
            # BSD stat (macOS)
            folder_mtime=$(stat -f %m "$subfolder" 2>/dev/null)
        fi
        
        if [ -z "$folder_mtime" ]; then
            log WARN "Could not get modification time for: $subfolder"
            continue
        fi
        
        # Calculate age of the subfolder
        age=$((current_time - folder_mtime))
        
        # Remove if older than MAX_AGE
        if [ "$age" -gt "$MAX_AGE" ]; then
            log WARN "Removing old subfolder (age: ${age}s): $(basename "$subfolder")"
            if rm -rf "$subfolder" 2>/dev/null; then
                log INFO "Successfully removed: $(basename "$subfolder")"
                removed_count=$((removed_count + 1))
            else
                log ERROR "Failed to remove: $(basename "$subfolder")"
            fi
        fi
    done
    
    log INFO "Check complete - Checked: $checked_count, Removed: $removed_count"
    log INFO "Next check in ${CHECK_INTERVAL}s..."
    
    # Sleep until next check
    sleep "$CHECK_INTERVAL"
done
