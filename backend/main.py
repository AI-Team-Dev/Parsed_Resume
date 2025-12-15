from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import sys
import asyncio
import uuid
import json
import shutil
from typing import Dict, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.parser_service import process_folder
from backend.config import GROK_API_KEYS

app = FastAPI(title="Resume Parser API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory progress tracking
progress_tracker: Dict[str, dict] = {}

@app.post("/api/process")
async def process_resumes(input_folder: str, output_path: str, append: bool = False, job_id: str = None):
    """
    Process resumes from input folder and save to output path
    
    Args:
        input_folder: Path to folder containing resume files
        output_path: Path where output Excel file should be saved
        append: If True, append to existing file. If False, create new file.
        job_id: Optional job ID for progress tracking. If not provided, one will be generated.
    """
    if not os.path.exists(input_folder):
        raise HTTPException(status_code=404, detail=f"Input folder not found: {input_folder}")
    
    if not os.path.isdir(input_folder):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {input_folder}")
    
    # Generate job_id if not provided
    if not job_id:
        job_id = str(uuid.uuid4())
    
    # Initialize progress tracking
    files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    progress_tracker[job_id] = {
        "status": "processing",
        "total_files": len(files),
        "processed_files": 0,
        "failed_files": 0,
        "file_status": {f: "pending" for f in files},  # pending, processing, success, failed
        "current_file": None,
        "message": "",
        "output_path": output_path,
        "start_time": datetime.now().isoformat(),
        "end_time": None
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else "."
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Progress callback
    def progress_callback(current, total):
        if job_id in progress_tracker:
            # Update total if needed
            progress_tracker[job_id]["total_files"] = total
            # Note: processed_files count is calculated from file_status, not from this callback
    
    # Status callback to track individual file status
    def status_callback(message):
        if job_id not in progress_tracker:
            return
        
        progress_tracker[job_id]["message"] = message
        
        # Update file status based on message patterns
        # Pattern: "[SUCCESS] Parsed filename.pdf"
        if "[SUCCESS] Parsed" in message:
            parts = message.split("Parsed ")
            if len(parts) > 1:
                filename = parts[1].strip()
                if filename in progress_tracker[job_id]["file_status"]:
                    old_status = progress_tracker[job_id]["file_status"][filename]
                    progress_tracker[job_id]["file_status"][filename] = "success"
                    # Recalculate counts from file_status
                    file_status = progress_tracker[job_id]["file_status"]
                    progress_tracker[job_id]["processed_files"] = sum(1 for s in file_status.values() if s == "success")
                    progress_tracker[job_id]["failed_files"] = sum(1 for s in file_status.values() if s == "failed")
        
        # Pattern: "[ERROR] Failed to parse filename.pdf" or "[ERROR] Failed to process filename.pdf"
        elif "[ERROR]" in message:
            # Try to extract filename from error message
            for filename in progress_tracker[job_id]["file_status"]:
                if filename in message:
                    old_status = progress_tracker[job_id]["file_status"][filename]
                    if old_status in ["processing", "pending"]:
                        progress_tracker[job_id]["file_status"][filename] = "failed"
                        # Recalculate counts from file_status
                        file_status = progress_tracker[job_id]["file_status"]
                        progress_tracker[job_id]["processed_files"] = sum(1 for s in file_status.values() if s == "success")
                        progress_tracker[job_id]["failed_files"] = sum(1 for s in file_status.values() if s == "failed")
                        break
        
        # Pattern: "[WARNING] Skipped filename.pdf"
        elif "[WARNING] Skipped" in message:
            parts = message.split("Skipped ")
            if len(parts) > 1:
                filename = parts[1].strip()
                if filename in progress_tracker[job_id]["file_status"]:
                    old_status = progress_tracker[job_id]["file_status"][filename]
                    if old_status in ["processing", "pending"]:
                        progress_tracker[job_id]["file_status"][filename] = "failed"
                        # Recalculate counts from file_status
                        file_status = progress_tracker[job_id]["file_status"]
                        progress_tracker[job_id]["processed_files"] = sum(1 for s in file_status.values() if s == "success")
                        progress_tracker[job_id]["failed_files"] = sum(1 for s in file_status.values() if s == "failed")
        
        # Pattern: "Processing: filename.pdf (1/10)"
        elif "Processing:" in message:
            parts = message.split("Processing: ")
            if len(parts) > 1:
                filename_part = parts[1].split(" (")[0].strip()
                if filename_part in progress_tracker[job_id]["file_status"]:
                    old_status = progress_tracker[job_id]["file_status"][filename_part]
                    if old_status == "pending":
                        progress_tracker[job_id]["file_status"][filename_part] = "processing"
                    progress_tracker[job_id]["current_file"] = filename_part
    
    # Process files in background thread
    def process():
        try:
            return process_folder(
                input_folder,
                output_path,
                api_key=GROK_API_KEYS[0] if GROK_API_KEYS else None,
                append=append,
                progress_callback=progress_callback,
                status_callback=status_callback
            )
        finally:
            # Mark as completed
            if job_id in progress_tracker:
                progress_tracker[job_id]["status"] = "completed"
                progress_tracker[job_id]["end_time"] = datetime.now().isoformat()
                progress_tracker[job_id]["current_file"] = None
                # Final count update
                file_status = progress_tracker[job_id]["file_status"]
                progress_tracker[job_id]["processed_files"] = sum(1 for s in file_status.values() if s == "success")
                progress_tracker[job_id]["failed_files"] = sum(1 for s in file_status.values() if s == "failed")
    
    # Start processing in background
    asyncio.create_task(asyncio.to_thread(process))
    
    return {
        "status": "started",
        "job_id": job_id,
        "message": f"Processing started for {len(files)} files",
        "total_files": len(files)
    }

@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    """Get progress for a specific job"""
    if job_id not in progress_tracker:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return progress_tracker[job_id]

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload resume files to the server
    
    Returns:
        Path to the folder containing uploaded files
    """
    # Create upload directory
    upload_dir = "/app/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create a unique session folder for this upload
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(upload_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    uploaded_files = []
    skipped_files = []
    
    for file in files:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.pdf', '.docx', '.doc']:
            skipped_files.append(file.filename)
            continue
        
        # Save file
        file_path = os.path.join(session_dir, file.filename)
        try:
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            uploaded_files.append(file.filename)
        except Exception as e:
            skipped_files.append(f"{file.filename} (error: {str(e)})")
    
    if not uploaded_files:
        raise HTTPException(
            status_code=400, 
            detail=f"No valid resume files uploaded. Supported formats: PDF, DOCX, DOC. Skipped: {', '.join(skipped_files) if skipped_files else 'none'}"
        )
    
    response = {
        "status": "success",
        "upload_folder": session_dir,
        "uploaded_files": uploaded_files,
        "count": len(uploaded_files)
    }
    
    if skipped_files:
        response["skipped_files"] = skipped_files
    
    return response

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Resume Parser API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
