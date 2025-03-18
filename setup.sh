#!/bin/bash
# Setup script for Wan2.1 API Server

set -e  # Exit on error

# Default configuration
MODEL="Wan2.1-T2V-1.3B"
USE_MODELSCOPE=false
PORT=3000
HOST="0.0.0.0"

# Colors for pretty output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo -e "${BLUE}Wan2.1 API Server Setup${NC}"
    echo ""
    echo "This script helps set up the Wan2.1 API Server by installing dependencies and downloading model files."
    echo ""
    echo "Usage: ./setup.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --modelscope       Download model from ModelScope instead of Hugging Face"
    echo "  --model MODEL      Specify model to download (default: $MODEL)"
    echo "                     Available options: Wan2.1-T2V-1.3B, Wan2.1-T2V-14B,"
    echo "                     Wan2.1-I2V-14B-480P, Wan2.1-I2V-14B-720P"
    echo "  --port PORT        Port to run the API server on (default: $PORT)"
    echo "  --host HOST        Host interface to bind to (default: $HOST)"
    echo "  --help             Display this help message"
    echo ""
}

# Parse command-line options
while (( "$#" )); do
    case "$1" in
        --modelscope)
            USE_MODELSCOPE=true
            shift
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate model choice
if [[ ! "$MODEL" =~ ^Wan2\.1-(T2V-1\.3B|T2V-14B|I2V-14B-480P|I2V-14B-720P)$ ]]; then
    echo -e "${RED}Invalid model: $MODEL${NC}"
    echo "Please choose one of: Wan2.1-T2V-1.3B, Wan2.1-T2V-14B, Wan2.1-I2V-14B-480P, Wan2.1-I2V-14B-720P"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Create required directories
mkdir -p outputs static

echo -e "\n${BLUE}=== Wan2.1 API Server Setup ===${NC}\n"

# Step 1: Install dependencies
echo -e "${YELLOW}Step 1: Installing dependencies...${NC}"
pip install -r requirements.txt

# Step 2: Download model files
echo -e "\n${YELLOW}Step 2: Downloading model files (this may take a while)...${NC}"
if [ "$USE_MODELSCOPE" = true ]; then
    echo "Using ModelScope to download model..."
    if ! command_exists modelscope; then
        pip install modelscope
    fi
    modelscope download Wan-AI/$MODEL --local_dir ./$MODEL
else
    echo "Using Hugging Face to download model..."
    if ! command_exists huggingface-cli; then
        pip install "huggingface_hub[cli]"
    fi
    huggingface-cli download Wan-AI/$MODEL --local-dir ./$MODEL
fi

# Step 3: Organize model files
echo -e "\n${YELLOW}Step 3: Organizing model files...${NC}"
if [ -d "./$MODEL/google/umt5-xxl" ]; then
    echo "Setting up tokenizer directory..."
    mkdir -p ./$MODEL/tokenizer
    cp ./$MODEL/google/umt5-xxl/* ./$MODEL/tokenizer/
fi

# Step 4: Check if setup was successful
echo -e "\n${YELLOW}Step 4: Verifying setup...${NC}"

# Check for essential files
if [ -f "./$MODEL/models_t5_umt5-xxl-enc-bf16.pth" ] && [ -f "./$MODEL/Wan2.1_VAE.pth" ]; then
    echo -e "${GREEN}Model files are correctly downloaded.${NC}"
else
    echo -e "${RED}Warning: Some model files might be missing!${NC}"
    echo "Expected files in ./$MODEL/:"
    echo "  - models_t5_umt5-xxl-enc-bf16.pth"
    echo "  - Wan2.1_VAE.pth"
    echo "Please check the model directory and try downloading again if needed."
fi

# Make start script executable
chmod +x start_api_server.sh

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "\nTo start the API server, run:"
echo -e "${BLUE}./start_api_server.sh --port $PORT --host $HOST --ckpt_dir ./$MODEL${NC}"
echo ""
echo -e "The web interface will be available at: ${BLUE}http://$HOST:$PORT/${NC}"
echo -e "Note: If using 0.0.0.0 as host, access via ${BLUE}http://localhost:$PORT/${NC} or your machine's IP address."
echo ""