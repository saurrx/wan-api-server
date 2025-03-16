#!/bin/bash
# Start the Wan2.1 API Server

# Default values
PORT=3000
HOST="0.0.0.0"
CKPT_DIR="./Wan2.1-T2V-1.3B"

# Parse command-line arguments
while (( "$#" )); do
  case "$1" in
    --port)
      PORT=$2
      shift 2
      ;;
    --host)
      HOST=$2
      shift 2
      ;;
    --ckpt_dir)
      CKPT_DIR=$2
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--port PORT] [--host HOST] [--ckpt_dir CHECKPOINT_DIR]"
      exit 1
      ;;
  esac
done

# Create directory for static files if it doesn't exist
mkdir -p static

# Create outputs directory for videos
mkdir -p outputs

# Start the API server
echo "Starting Wan2.1 API Server on $HOST:$PORT..."
echo "Using model checkpoint directory: $CKPT_DIR"

python api_server.py --port $PORT --host $HOST --ckpt_dir $CKPT_DIR