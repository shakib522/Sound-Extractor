
import logging
from pathlib import Path
import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .audio_processor import AudioProcessor
from .models import AudioExtractionResponse, ProcessingStatus, SeparationType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Audio Extraction API",
    description="API for extracting vocals and music from audio files using ML models",
    version="1.0.0"
)

# Add CORS middleware for mobile app integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize audio processor
audio_processor = AudioProcessor()

# Create necessary directories
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Initializing Audio Extraction API...")
    try:
        await audio_processor.initialize_models()
        logger.info("API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Audio Extraction API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_available": True
    }


@app.post("/extract-audio", response_model=AudioExtractionResponse)
async def extract_audio(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        separation_type: SeparationType = SeparationType.VOCALS_ACCOMPANIMENT,
        quality: str = "high"
):
    """
    Extract vocals and music from uploaded audio file
    
    - **file**: Audio file to process (supports: mp3, wav, m4a, flac)
    - **separation_type**: Type of separation to perform
    - **quality**: Output quality (high, medium, low)
    """

    # Validate file type
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
    filename = file.filename or 'uploaded_file'
    file_extension = Path(filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 50MB"
        )

    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        logger.info(f"File uploaded: {file_path}")

        # Start audio processing
        task_id = await audio_processor.process_audio(
            str(file_path),
            separation_type.value,
            quality
        )

        return AudioExtractionResponse(
            task_id=task_id,
            status="processing",
            message="Audio extraction started successfully"
        )

    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{task_id}", response_model=ProcessingStatus)
async def get_processing_status(task_id: str):
    """Get the status of an audio processing task"""

    task_status = audio_processor.get_task_status(task_id)

    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    return ProcessingStatus(
        task_id=task_id,
        status=task_status["status"],
        progress=task_status.get("progress"),
        message=task_status.get("message"),
        download_urls=task_status.get("download_urls")
    )


@app.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """Download a processed audio file"""

    task_status = audio_processor.get_task_status(task_id)

    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")

    # Construct file path
    file_path = Path("outputs") / task_id / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="audio/wav"
    )


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a processing task and its files"""

    task_status = audio_processor.get_task_status(task_id)

    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    # Clean up task and files
    audio_processor.cleanup_task(task_id)

    return {"message": "Task deleted successfully"}


@app.get("/supported-formats")
async def get_supported_formats():
    """Get supported audio formats and separation types"""
    return {
        "supported_formats": ["mp3", "wav", "m4a", "flac", "ogg"],
        "separation_types": [
            {
                "name": "vocals_accompaniment",
                "description": "Separate vocals from background music",
                "output_files": 2
            },
            {
                "name": "vocals_drums_bass_other",
                "description": "Separate into vocals, drums, bass, and other instruments",
                "output_files": 4
            },
            {
                "name": "vocals_drums_bass_piano_other",
                "description": "Separate into vocals, drums, bass, piano, and other instruments",
                "output_files": 5
            }
        ],
        "quality_options": [
            {
                "name": "high",
                "description": "Original quality (larger files)"
            },
            {
                "name": "medium",
                "description": "Reduced quality (22050 Hz, smaller files)"
            },
            {
                "name": "low",
                "description": "Low quality (16000 Hz, smallest files)"
            }
        ]
    }


# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}


@app.exception_handler(413)
async def file_too_large_handler(request, exc):
    return {"error": "File too large", "detail": "Maximum file size is 50MB"}
