from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class SeparationType(str, Enum):
    VOCALS_ACCOMPANIMENT = "vocals_accompaniment"
    VOCALS_DRUMS_BASS_OTHER = "vocals_drums_bass_other"
    VOCALS_DRUMS_BASS_PIANO_OTHER = "vocals_drums_bass_piano_other"

class AudioExtractionRequest(BaseModel):
    separation_type: SeparationType = SeparationType.VOCALS_ACCOMPANIMENT
    quality: str = "high"  # high, medium, low

class AudioExtractionResponse(BaseModel):
    task_id: str
    status: str
    message: str
    download_urls: Optional[List[str]] = None

class ProcessingStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[float] = None
    message: Optional[str] = None
    download_urls: Optional[List[str]] = None 