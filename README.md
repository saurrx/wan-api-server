# Wan2.1 Video Generation API Server

<p align="center">
  <img src="assets/logo.png" width="300"/>
</p>

This repository provides a RESTful API server for Wan2.1, a state-of-the-art video generation model. The API server makes it easy to integrate Wan2.1's video generation capabilities into your applications, allowing you to generate high-quality videos from text prompts.

## Features

- **RESTful API**: Simple HTTP interface for video generation
- **Queue-Based Processing**: Requests are processed one at a time for optimal resource usage
- **Text-to-Video Generation**: Generate videos from text descriptions
- **Prompt Extension**: Optional feature to enhance prompt details for better results
- **Status Tracking**: Monitor generation progress and queue position
- **Web Client Interface**: Simple web UI for submitting requests and downloading results

## Requirements

- Python 3.8+
- CUDA-compatible GPU with at least 8GB VRAM (16GB+ recommended)
- Approximately 35GB of disk space for model files

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/wan2.1-api.git
cd wan2.1-api
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download the Model

Download the required model files using Hugging Face CLI:

```bash
pip install "huggingface_hub[cli]"
huggingface-cli download Wan-AI/Wan2.1-T2V-1.3B --local-dir ./Wan2.1-T2V-1.3B
```

Or using ModelScope:

```bash
pip install modelscope
modelscope download Wan-AI/Wan2.1-T2V-1.3B --local_dir ./Wan2.1-T2V-1.3B
```

### 4. Prepare the Model Files

Ensure the tokenizer files are correctly placed:

```bash
mkdir -p ./Wan2.1-T2V-1.3B/tokenizer
cp ./Wan2.1-T2V-1.3B/google/umt5-xxl/* ./Wan2.1-T2V-1.3B/tokenizer/
```

### 5. Start the API Server

```bash
./start_api_server.sh
```

By default, the server runs on port 3000. You can customize this with command-line options:

```bash
./start_api_server.sh --port 8080 --host 127.0.0.1
```

### 6. Access the Web Interface

Open your browser and navigate to:

```
http://localhost:3000/
```

## API Usage

### Generate a Video

**Request:**

```bash
curl -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Two anthropomorphic cats in comfy boxing gear and bright gloves fight intensely on a spotlighted stage",
    "size": "832*480",
    "sample_steps": 50,
    "guide_scale": 6.0,
    "use_prompt_extend": true,
    "prompt_extend_target_lang": "en"
  }'
```

**Response:**

```json
{
  "job_id": "unique-job-identifier",
  "status": "queued"
}
```

### Check Job Status

```bash
curl http://localhost:3000/api/jobs/unique-job-identifier
```

### Download Generated Video

Once job status is "completed":

```bash
curl -o output.mp4 http://localhost:3000/api/jobs/unique-job-identifier/video
```

## Python Client Example

```python
import requests
import time

server_url = "http://localhost:3000"
prompt = "A cat and a dog baking a cake together in a kitchen"

# Submit job
response = requests.post(
    f"{server_url}/api/generate",
    json={
        "prompt": prompt,
        "size": "832*480",
        "sample_steps": 50,
        "guide_scale": 6.0,
        "use_prompt_extend": True
    }
)
job_id = response.json()["job_id"]
print(f"Job submitted with ID: {job_id}")

# Poll for completion
while True:
    response = requests.get(f"{server_url}/api/jobs/{job_id}")
    status = response.json()["status"]
    
    if status == "completed":
        print("Job completed!")
        # Download the video
        with open("output.mp4", "wb") as f:
            video = requests.get(f"{server_url}/api/jobs/{job_id}/video")
            f.write(video.content)
        print("Video downloaded to output.mp4")
        break
    elif status == "failed":
        print(f"Job failed: {response.json().get('error')}")
        break
    else:
        print(f"Status: {status}")
        time.sleep(10)
```

Or use the included client script:

```bash
python api_client_example.py --prompt "Your video description" --output output.mp4
```

## Advanced Options

### Using Prompt Extension

The API supports two methods of prompt extension to improve generation quality:

1. **Local Qwen Model**:
   The default method which uses a local Qwen LLM for prompt extension.

2. **DashScope API**:
   To use Alibaba Cloud's DashScope API for prompt extension, set the `DASH_API_KEY` environment variable:

   ```bash
   export DASH_API_KEY=your_api_key
   ./start_api_server.sh
   ```

For international users of Alibaba Cloud, also set:

```bash
export DASH_API_URL='https://dashscope-intl.aliyuncs.com/api/v1'
```

### Server Configuration Options

The start script supports the following options:

```
--port PORT        Port to run the server on (default: 3000)
--host HOST        Host interface to bind to (default: 0.0.0.0)
--ckpt_dir DIR     Path to model checkpoint directory (default: ./Wan2.1-T2V-1.3B)
```

## Performance Notes

- Video generation takes approximately 6-10 minutes per video
- Memory usage varies based on model size and resolution
- For 1.3B model, 8GB GPU VRAM is sufficient for 480p generation
- For higher resolutions or faster generation, consider using multiple GPUs

## Model Information

This API server uses the Wan2.1 Text-to-Video model developed by the Alibaba Wan Team. Multiple model versions are available:

- **T2V-1.3B**: Smallest model, good for consumer GPUs
- **T2V-14B**: Higher quality, requires more GPU memory
- **I2V-14B**: Image-to-video model (requires modifications to use)

By default, this API server uses the T2V-1.3B model for optimal balance of quality and performance.

## Troubleshooting

### Common Issues

**API server fails to start**:
- Check if port 3000 is already in use
- Verify model files are correctly downloaded
- Ensure all dependencies are installed

**Out of memory errors**:
- Reduce video resolution by changing the `size` parameter
- Lower `sample_steps` (reduces quality but uses less memory)
- Add `--offload_model True` and `--t5_cpu` to the generate.py command

**Generation failures**:
- Check API server logs for detailed error messages
- Verify proper model directory structure
- Ensure model files are fully downloaded

## License

See [LICENSE.txt](LICENSE.txt) for usage terms and conditions.

## Acknowledgments

This project uses the Wan2.1 video generation model developed by the Alibaba Wan Team. Visit the [official Wan2.1 repository](https://github.com/Wan-Video/Wan2.1) for more information about the model itself.