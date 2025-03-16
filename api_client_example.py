#!/usr/bin/env python
# Example client for Wan2.1 API Server
import argparse
import json
import time
import requests
from pathlib import Path

def submit_job(server_url, prompt, params=None):
    """Submit a new video generation job"""
    if params is None:
        params = {}
    
    # Prepare request data
    data = {
        "prompt": prompt,
        **params
    }
    
    # Submit job
    response = requests.post(
        f"{server_url}/api/generate",
        json=data
    )
    
    if response.status_code != 200:
        print(f"Error submitting job: {response.text}")
        return None
    
    result = response.json()
    print(f"Job submitted successfully! Job ID: {result['job_id']}")
    return result["job_id"]

def check_job_status(server_url, job_id):
    """Check the status of a job"""
    response = requests.get(f"{server_url}/api/jobs/{job_id}")
    
    if response.status_code != 200:
        print(f"Error checking job status: {response.text}")
        return None
    
    result = response.json()
    status = result["status"]
    
    if status == "queued":
        queue_pos = result.get("queue_position", "unknown")
        print(f"Job is queued (position: {queue_pos})")
    elif status == "processing":
        print("Job is currently processing...")
    elif status == "completed":
        print(f"Job completed successfully!")
    elif status == "failed":
        print(f"Job failed: {result.get('error', 'Unknown error')}")
    
    return result

def download_video(server_url, job_id, output_path):
    """Download the generated video file"""
    response = requests.get(
        f"{server_url}/api/jobs/{job_id}/video",
        stream=True
    )
    
    if response.status_code != 200:
        print(f"Error downloading video: {response.text}")
        return False
    
    # Save the video file
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Video downloaded to {output_path}")
    return True

def poll_until_complete(server_url, job_id, output_path, poll_interval=10):
    """Poll the job status until it completes"""
    print("Waiting for job to complete (this will take 6-10 minutes)...")
    
    while True:
        result = check_job_status(server_url, job_id)
        
        if result is None:
            print("Error checking job status. Retrying...")
        elif result["status"] == "completed":
            print("Job completed! Downloading video...")
            download_video(server_url, job_id, output_path)
            return True
        elif result["status"] == "failed":
            print(f"Job failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Wait before polling again
        print("Still waiting... (checking again in {} seconds)".format(poll_interval))
        time.sleep(poll_interval)

def parse_args():
    parser = argparse.ArgumentParser(description="Wan2.1 API Client Example")
    parser.add_argument(
        "--server",
        type=str,
        default="http://localhost:3000",
        help="API server URL"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Two anthropomorphic cats in comfy boxing gear and bright gloves fight intensely on a spotlighted stage",
        help="Text prompt for video generation"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output_video.mp4",
        help="Output path for downloaded video"
    )
    parser.add_argument(
        "--size",
        type=str,
        default="832*480",
        help="Video size in format width*height"
    )
    parser.add_argument(
        "--sample_steps",
        type=int,
        default=50,
        help="Number of sampling steps"
    )
    parser.add_argument(
        "--guide_scale",
        type=float,
        default=6.0,
        help="Guidance scale"
    )
    parser.add_argument(
        "--use_prompt_extend",
        action="store_true",
        help="Enable prompt extension"
    )
    parser.add_argument(
        "--prompt_extend_target_lang",
        type=str,
        default="zh",
        choices=["zh", "en"],
        help="Target language for prompt extension (zh or en)"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Prepare parameters
    params = {
        "size": args.size,
        "sample_steps": args.sample_steps,
        "guide_scale": args.guide_scale,
        "use_prompt_extend": args.use_prompt_extend,
        "prompt_extend_target_lang": args.prompt_extend_target_lang
    }
    
    # Submit the job
    job_id = submit_job(args.server, args.prompt, params)
    
    if job_id:
        # Poll until complete
        poll_until_complete(args.server, job_id, args.output)