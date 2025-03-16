# Wan2.1 Video Generation API Server

This API server provides a simple interface for generating videos using the Wan2.1 model. It processes video generation requests one by one in a queue.

## Features

- RESTful API for video generation requests
- Sequential processing queue (one video at a time)
- Web interface for easy submission and monitoring
- Python client example for programmatic access
- Status tracking and queue position updates
- Video download functionality
- Uses generate.py directly as a subprocess (no direct model imports)

## Prerequisites

- Python 3.8+
- Wan2.1 model and dependencies installed
- Flask and Flask-CORS installed (`pip install flask flask-cors`)

## Starting the Server

Run the included start script:

```bash
./start_api_server.sh
```

Options:

```
--port PORT        Port to run the server on (default: 3000)
--host HOST        Host interface to bind to (default: 0.0.0.0)
--ckpt_dir DIR     Path to Wan2.1 model checkpoint directory (default: ./Wan2.1-T2V-1.3B)
```

## Web Interface

Once the server is running, you can access the web interface at:

```
http://localhost:3000/
```

The interface allows you to:
- Enter a text prompt
- Configure generation parameters
- Submit generation requests
- Monitor job status
- Download completed videos

## API Endpoints

### Submit a Video Generation Job

```
POST /api/generate
```

Request body:
```json
{
  "prompt": "Description of the video to generate",
  "size": "832*480",
  "sample_steps": 50,
  "sample_shift": 5.0,
  "guide_scale": 6.0,
  "seed": -1,
  "use_prompt_extend": true,
  "prompt_extend_target_lang": "zh" // Must be either "zh" or "en"
}
```

Response:
```json
{
  "job_id": "unique-job-identifier",
  "status": "queued"
}
```

### Check Job Status

```
GET /api/jobs/{job_id}
```

Response:
```json
{
  "job_id": "unique-job-identifier",
  "prompt": "Original prompt",
  "params": { ... },
  "status": "queued|processing|completed|failed",
  "queue_position": 0,
  "created_at": "ISO timestamp",
  "started_at": "ISO timestamp or null",
  "completed_at": "ISO timestamp or null",
  "output_path": "path/to/video.mp4 or null",
  "error": "Error message or null"
}
```

### Download Generated Video

```
GET /api/jobs/{job_id}/video
```

Returns the video file if generation is complete.

### List All Jobs

```
GET /api/jobs
```

Returns a list of all jobs with their status.

## Using the Python Client

An example Python client is included to demonstrate API usage:

```bash
python api_client_example.py --prompt "Your video description" --output output.mp4
```

Options:
```
--server URL       API server URL (default: http://localhost:3000)
--prompt TEXT      Text prompt for video generation
--output FILE      Output path for downloaded video
--size SIZE        Video size (default: 832*480)
--sample_steps N   Number of sampling steps (default: 50)
--guide_scale N    Guidance scale (default: 6.0)
--use_prompt_extend Enable prompt extension
```

## Notes

- Video generation takes approximately 6-10 minutes per video
- All videos are processed sequentially (one at a time)
- Generated videos are stored in the `outputs` directory
- The server must have access to the Wan2.1 model and checkpoint files