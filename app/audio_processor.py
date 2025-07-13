import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
import librosa
import soundfile as sf
import numpy as np
import torch
import torchaudio
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.processing_tasks: Dict[str, Dict] = {}
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
        
    async def initialize_models(self):
        """Initialize the ML models for audio separation"""
        try:
            logger.info("Initializing Spleeter models...")
            # Check if spleeter is available
            result = subprocess.run([sys.executable, "-m", "spleeter", "--help"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Spleeter is available and ready to use")
            else:
                logger.warning("Spleeter not available, will use basic separation")
        except Exception as e:
            logger.error(f"Failed to initialize Spleeter: {e}")
            logger.info("Will use basic audio processing instead")
    
    async def process_audio(
        self, 
        input_file_path: str, 
        separation_type: str = "vocals_accompaniment",
        quality: str = "high"
    ) -> str:
        """
        Process audio file and separate it into multiple tracks
        
        Args:
            input_file_path: Path to input audio file
            separation_type: Type of separation to perform
            quality: Quality setting for processing
            
        Returns:
            task_id: Unique identifier for the processing task
        """
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        self.processing_tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Task created",
            "input_file": input_file_path,
            "separation_type": separation_type,
            "quality": quality
        }
        
        # Start processing in background
        asyncio.create_task(self._process_audio_async(task_id))
        
        return task_id
    
    async def _process_audio_async(self, task_id: str):
        """Background processing of audio file"""
        try:
            task = self.processing_tasks[task_id]
            task["status"] = "processing"
            task["progress"] = 0.1
            task["message"] = "Loading audio file..."
            
            # Load and validate audio file
            input_path = Path(task["input_file"])
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Create output directory for this task
            task_output_dir = self.output_dir / task_id
            task_output_dir.mkdir(exist_ok=True)
            
            task["progress"] = 0.2
            task["message"] = "Initializing separation model..."
            
            task["progress"] = 0.3
            task["message"] = "Separating audio tracks..."
            
            # Perform audio separation using Spleeter
            output_files = await self._separate_audio_spleeter(
                str(input_path), 
                str(task_output_dir), 
                task["separation_type"]
            )
            
            task["progress"] = 0.8
            task["message"] = "Post-processing audio files..."
            
            # Post-process and optimize output files
            processed_files = await self._post_process_outputs(output_files, task["quality"])
            
            task["progress"] = 1.0
            task["status"] = "completed"
            task["message"] = "Processing completed successfully"
            task["download_urls"] = processed_files
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            task = self.processing_tasks[task_id]
            task["status"] = "failed"
            task["message"] = f"Processing failed: {str(e)}"
    
    async def _separate_audio_spleeter(self, input_path: str, output_dir: str, separation_type: str) -> List[str]:
        """Separate audio using Spleeter"""
        try:
            # Map separation types to Spleeter models
            model_map = {
                "vocals_accompaniment": "spleeter:2stems",
                "vocals_drums_bass_other": "spleeter:4stems",
                "vocals_drums_bass_piano_other": "spleeter:5stems"
            }
            
            model = model_map.get(separation_type, "spleeter:2stems")
            
            # Run Spleeter separation with correct command structure
            cmd = [
                sys.executable, "-m", "spleeter", "separate",
                "--output_path", output_dir,
                "--params_filename", model,
                input_path
            ]
            
            logger.info(f"Running Spleeter command: {' '.join(cmd)}")
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Spleeter failed: {stderr.decode()}")
                logger.error(f"Spleeter stdout: {stdout.decode()}")
                # Fallback to basic separation
                return await self._basic_audio_separation(input_path, output_dir, separation_type)
            
            # Find output files
            output_files = []
            output_path = Path(output_dir)
            
            # Spleeter creates a subdirectory with the input filename (without extension)
            input_filename = Path(input_path).stem
            spleeter_output_dir = output_path / input_filename
            
            if spleeter_output_dir.exists():
                for audio_file in spleeter_output_dir.rglob("*.wav"):
                    if audio_file.is_file():
                        output_files.append(str(audio_file))
            
            logger.info(f"Spleeter output files: {output_files}")
            return output_files
            
        except Exception as e:
            logger.error(f"Spleeter separation failed: {e}")
            # Fallback to basic separation
            return await self._basic_audio_separation(input_path, output_dir, separation_type)
    
    async def _basic_audio_separation(self, input_path: str, output_dir: str, separation_type: str) -> List[str]:
        """Basic audio separation using librosa (fallback method)"""
        logger.info("Using basic audio separation as fallback")
        
        # Load audio
        audio, sr = librosa.load(input_path, sr=None)
        
        # Simple separation: split into frequency bands
        # This is a basic approximation - not as good as ML models
        if separation_type == "vocals_accompaniment":
            # Split into high and low frequency components
            vocals = librosa.effects.harmonic(audio)
            accompaniment = audio - vocals
            
            # Save files
            vocals_path = Path(output_dir) / "vocals.wav"
            accompaniment_path = Path(output_dir) / "accompaniment.wav"
            
            sf.write(str(vocals_path), vocals, sr)
            sf.write(str(accompaniment_path), accompaniment, sr)
            
            return [str(vocals_path), str(accompaniment_path)]
        else:
            # For other separation types, create basic splits
            segments = np.array_split(audio, 4)
            output_files = []
            
            for i, segment in enumerate(segments):
                segment_path = Path(output_dir) / f"segment_{i+1}.wav"
                sf.write(str(segment_path), segment, sr)
                output_files.append(str(segment_path))
            
            return output_files
    
    async def _post_process_outputs(self, output_files: List[str], quality: str) -> List[str]:
        """Post-process the separated audio files"""
        processed_files = []
        
        for file_path in output_files:
            if quality == "high":
                # Keep original quality
                processed_files.append(file_path)
            else:
                # Reduce quality for smaller file size
                optimized_path = await self._optimize_audio_quality(file_path, quality)
                processed_files.append(optimized_path)
        
        return processed_files
    
    async def _optimize_audio_quality(self, file_path: str, quality: str) -> str:
        """Optimize audio quality for smaller file size"""
        # Load audio
        audio, sr = librosa.load(file_path, sr=None)
        
        # Reduce quality based on setting
        if quality == "medium":
            # Reduce sample rate to 22050 Hz
            audio = librosa.resample(audio, orig_sr=sr, target_sr=22050)
            sr = 22050
        elif quality == "low":
            # Reduce sample rate to 16000 Hz
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            sr = 16000
        
        # Save optimized file
        file_path_obj = Path(file_path)
        optimized_path = file_path_obj.parent / f"{file_path_obj.stem}_optimized{file_path_obj.suffix}"
        sf.write(str(optimized_path), audio, sr)
        
        return str(optimized_path)
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a processing task"""
        return self.processing_tasks.get(task_id)
    
    def cleanup_task(self, task_id: str):
        """Clean up task data and files"""
        if task_id in self.processing_tasks:
            # Remove task data
            del self.processing_tasks[task_id]
            
            # Remove output files
            task_output_dir = self.output_dir / task_id
            if task_output_dir.exists():
                import shutil
                shutil.rmtree(task_output_dir) 