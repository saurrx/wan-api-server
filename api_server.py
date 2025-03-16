#!/usr/bin/env python
# Copyright 2024-2025 The Alibaba Wan Team Authors. All rights reserved.
import argparse
import logging
import os
import sys
import uuid
import time
import json
import threading
import queue
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)]
)

# Global variables
app = Flask(__name__)
CORS(app)

# Job management - single processing queue
job_queue = queue.Queue()
jobs = {}
jobs_lock = threading.Lock()
worker_thread = None
processing_event = threading.Event()

class JobStatus:
    QUEUED = "queued"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class Job:
    def __init__(self, job_id: str, prompt: str, params: Dict):
        self.job_id = job_id
        self.prompt = prompt
        self.params = params
        self.status = JobStatus.QUEUED
        self.queue_position = None
        self.created_at = datetime.now().isoformat()
        self.started_at = None
        self.completed_at = None
        self.output_path = None
        self.error = None
        
    def to_dict(self):
        result = {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "params": self.params,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output_path": self.output_path,
            "error": self.error
        }
        
        # Only include queue position for queued jobs
        if self.status == JobStatus.QUEUED and self.queue_position is not None:
            result["queue_position"] = self.queue_position
            
        return result

def update_queue_positions():
    """Update the queue position for all queued jobs"""
    queued_jobs = [job_id for job_id in jobs.keys() 
                  if jobs[job_id].status == JobStatus.QUEUED]
    
    # Sort by creation time
    queued_jobs.sort(key=lambda job_id: jobs[job_id].created_at)
    
    # Update positions
    for i, job_id in enumerate(queued_jobs):
        jobs[job_id].queue_position = i

def process_job_queue():
    """Worker function that processes jobs sequentially using generate.py"""
    global jobs
    
    while True:
        try:
            # Wait for a job to be available
            job_id = job_queue.get()
            
            # Process the job
            with jobs_lock:
                if job_id not in jobs:
                    logging.error(f"Job {job_id} not found in jobs dictionary")
                    job_queue.task_done()
                    continue
                
                job = jobs[job_id]
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now().isoformat()
                update_queue_positions()
            
            # Set event to indicate processing has started
            processing_event.set()
            
            logging.info(f"Processing job {job_id} with prompt: {job.prompt}")
            
            try:
                # Extract parameters with defaults
                prompt = job.prompt
                params = job.params
                size = params.get("size", "832*480")
                sample_steps = params.get("sample_steps", 50)
                sample_shift = params.get("sample_shift", 5.0)
                guide_scale = params.get("guide_scale", 6.0)
                seed = params.get("seed", -1)
                use_prompt_extend = params.get("use_prompt_extend", True)
                prompt_extend_method = params.get("prompt_extend_method", "local_qwen")
                prompt_extend_target_lang = params.get("prompt_extend_target_lang", "zh")
                ckpt_dir = params.get("ckpt_dir", "./Wan2.1-T2V-1.3B")
                
                # Create output directory if it doesn't exist
                output_dir = Path("outputs")
                output_dir.mkdir(exist_ok=True)
                
                # Create a unique output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{job_id}_{timestamp}.mp4"
                output_path = output_dir / output_filename
                
                # Construct the generate.py command
                cmd = [
                    "python", "generate.py",
                    "--task", "t2v-1.3B",
                    "--size", size,
                    "--ckpt_dir", ckpt_dir,
                    "--prompt", prompt,
                    "--sample_steps", str(sample_steps),
                    "--sample_shift", str(sample_shift),
                    "--sample_guide_scale", str(guide_scale),
                    "--base_seed", str(seed),
                    "--save_file", str(output_path)
                ]
                
                if use_prompt_extend:
                    cmd.append("--use_prompt_extend")
                    cmd.extend(["--prompt_extend_method", prompt_extend_method])
                    cmd.extend(["--prompt_extend_target_lang", prompt_extend_target_lang])
                
                # Log the command being executed
                logging.info(f"Executing command: {' '.join(cmd)}")
                
                # Run the generate.py script as a subprocess
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for the process to complete
                stdout, stderr = process.communicate()
                
                # Check if the process was successful
                if process.returncode != 0:
                    raise Exception(f"Generate.py failed with error: {stderr}")
                
                # Log output
                logging.info(f"Generate.py output: {stdout}")
                
                # Verify the output file exists
                if not output_path.exists():
                    raise Exception(f"Output file {output_path} not found after generation")
                
                # Update job status
                with jobs_lock:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now().isoformat()
                    job.output_path = str(output_path)
                    update_queue_positions()
                
                logging.info(f"Job {job_id} completed successfully. Output saved to {output_path}")
                
            except Exception as e:
                logging.error(f"Error in job {job_id}: {str(e)}", exc_info=True)
                
                with jobs_lock:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now().isoformat()
                    job.error = str(e)
                    update_queue_positions()
            
            # Mark job as done in queue
            job_queue.task_done()
            
            # Reset processing event
            processing_event.clear()
            
        except Exception as e:
            logging.error(f"Error in worker thread: {str(e)}", exc_info=True)
            time.sleep(1)  # Prevent tight loop on errors

# API Routes
@app.route("/", methods=["GET"])
def index():
    """Serve the web client interface"""
    return send_from_directory('static', 'index.html')

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "queue_size": job_queue.qsize(),
        "processing": processing_event.is_set()
    })

@app.route("/api/generate", methods=["POST"])
def create_generation_job():
    """Create a new video generation job"""
    try:
        data = request.get_json()
        
        if not data or "prompt" not in data:
            return jsonify({"error": "Missing required field: prompt"}), 400
        
        prompt = data["prompt"]
        # Extract other parameters with defaults
        params = {
            "size": data.get("size", "832*480"),
            "sample_steps": data.get("sample_steps", 50),
            "sample_shift": data.get("sample_shift", 5.0),
            "guide_scale": data.get("guide_scale", 6.0),
            "seed": data.get("seed", -1),
            "use_prompt_extend": data.get("use_prompt_extend", True),
            "prompt_extend_method": data.get("prompt_extend_method", "local_qwen"),
            "prompt_extend_target_lang": data.get("prompt_extend_target_lang", "zh"),
            "ckpt_dir": data.get("ckpt_dir", "./Wan2.1-T2V-1.3B")
        }
        
        # Create a new job
        job_id = str(uuid.uuid4())
        job = Job(job_id, prompt, params)
        
        with jobs_lock:
            jobs[job_id] = job
            update_queue_positions()
        
        # Add job to the queue
        job_queue.put(job_id)
        
        return jsonify({"job_id": job_id, "status": job.status})
        
    except Exception as e:
        logging.error(f"Error creating job: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Get status of a specific job"""
    with jobs_lock:
        job = jobs.get(job_id)
        
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(job.to_dict())

@app.route("/api/jobs/<job_id>/video", methods=["GET"])
def get_job_video(job_id):
    """Get the generated video for a completed job"""
    with jobs_lock:
        job = jobs.get(job_id)
        
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    if job.status != JobStatus.COMPLETED:
        return jsonify({"error": "Video not ready", "status": job.status}), 400
    
    if not job.output_path or not os.path.exists(job.output_path):
        return jsonify({"error": "Video file not found"}), 404
    
    return send_file(job.output_path, mimetype="video/mp4")

@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    """List all jobs"""
    with jobs_lock:
        job_list = [job.to_dict() for job in jobs.values()]
    
    return jsonify({"jobs": job_list})

def start_worker_thread():
    """Start the worker thread that processes jobs one by one"""
    global worker_thread
    
    if worker_thread is None or not worker_thread.is_alive():
        worker_thread = threading.Thread(
            target=process_job_queue,
            daemon=True
        )
        worker_thread.start()
        logging.info("Worker thread started")

def parse_args():
    parser = argparse.ArgumentParser(description="Wan2.1 Video Generation API Server")
    parser.add_argument(
        "--port", 
        type=int, 
        default=3000, 
        help="Port to run the API server on"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0", 
        help="Host to run the API server on"
    )
    parser.add_argument(
        "--ckpt_dir", 
        type=str, 
        default="./Wan2.1-T2V-1.3B", 
        help="Path to the model checkpoint directory"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Create outputs directory
    Path("outputs").mkdir(exist_ok=True)
    
    # Start the worker thread
    start_worker_thread()
    
    # Start the Flask server
    logging.info(f"Starting API server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)