# Audio Extraction API

A FastAPI backend service for extracting vocals and music from audio files using free ML models (Spleeter).

## Features

- 🎵 **Audio Separation**: Extract vocals from background music
- 🎼 **Multiple Separation Types**: 
  - Vocals + Accompaniment (2 files)
  - Vocals + Drums + Bass + Other (4 files)
  - Vocals + Drums + Bass + Piano + Other (5 files)
- 📱 **Mobile App Ready**: RESTful API with CORS support
- 🚀 **Async Processing**: Background task processing with status tracking
- 🐳 **Docker Ready**: Easy deployment with Docker and Docker Compose
- 📊 **Quality Options**: High, medium, and low quality outputs

## Supported Audio Formats

- MP3
- WAV
- M4A
- FLAC
- OGG

## ML Models Used

- **Spleeter**: Free, open-source audio separation library by Deezer (primary)
- **Librosa**: Audio processing and analysis (fallback)
- **TorchAudio**: PyTorch-based audio processing

## Quick Start

### Prerequisites

- Python 3.10
- FFmpeg
- Docker (optional)

### Local Development

1. **Clone and setup**:
```bash
git clone <your-repo>
cd sound-extractor
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build and run with Docker Compose**:
```bash
docker-compose up --build
```

2. **Or build and run manually**:
```bash
docker build -t audio-extraction-api .
docker run -p 8000:8000 audio-extraction-api
```

## API Endpoints

### 1. Health Check
```http
GET /health
```

### 2. Upload and Extract Audio
```http
POST /extract-audio
Content-Type: multipart/form-data

Parameters:
- file: Audio file (required)
- separation_type: vocals_accompaniment | vocals_drums_bass_other | vocals_drums_bass_piano_other
- quality: high | medium | low
```

**Response**:
```json
{
  "task_id": "uuid-string",
  "status": "processing",
  "message": "Audio extraction started successfully"
}
```

### 3. Check Processing Status
```http
GET /status/{task_id}
```

**Response**:
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "progress": 1.0,
  "message": "Processing completed successfully",
  "download_urls": ["/path/to/vocals.wav", "/path/to/accompaniment.wav"]
}
```

### 4. Download Processed Files
```http
GET /download/{task_id}/{filename}
```

### 5. Get Supported Formats
```http
GET /supported-formats
```

### 6. Delete Task
```http
DELETE /tasks/{task_id}
```

## Mobile App Integration

### Example Usage (JavaScript/React Native)

```javascript
// Upload and process audio
const uploadAudio = async (audioFile) => {
  const formData = new FormData();
  formData.append('file', audioFile);
  formData.append('separation_type', 'vocals_accompaniment');
  formData.append('quality', 'high');

  const response = await fetch('http://your-api-url/extract-audio', {
    method: 'POST',
    body: formData,
  });

  const result = await response.json();
  return result.task_id;
};

// Check processing status
const checkStatus = async (taskId) => {
  const response = await fetch(`http://your-api-url/status/${taskId}`);
  return await response.json();
};

// Download processed files
const downloadFile = async (taskId, filename) => {
  const response = await fetch(`http://your-api-url/download/${taskId}/${filename}`);
  return await response.blob();
};
```

## Deployment Options

### 1. Cloud Deployment (AWS/GCP/Azure)

1. **Build Docker image**:
```bash
docker build -t audio-extraction-api .
```

2. **Push to container registry**:
```bash
docker tag audio-extraction-api your-registry/audio-extraction-api
docker push your-registry/audio-extraction-api
```

3. **Deploy to cloud platform** (example for AWS ECS):
```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name audio-extraction-api \
  --task-definition audio-extraction-api \
  --desired-count 1
```

### 2. VPS/Server Deployment

1. **SSH into your server**
2. **Clone the repository**
3. **Run with Docker Compose**:
```bash
docker-compose up -d
```

### 3. Local Production

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run with production server**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
MAX_FILE_SIZE=52428800  # 50MB in bytes

# Processing Configuration
DEFAULT_QUALITY=high
DEFAULT_SEPARATION_TYPE=vocals_accompaniment

# Storage Configuration
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
```

## Performance Considerations

- **Model Loading**: Spleeter models are loaded on startup (~500MB)
- **Processing Time**: Depends on file size and quality (typically 1-5 minutes)
- **Memory Usage**: ~2-4GB RAM recommended for processing
- **Storage**: Temporary files are stored in `uploads/` and `outputs/` directories

## Troubleshooting

### Common Issues

1. **Model download fails**:
   - Check internet connection
   - Ensure sufficient disk space (~1GB for models)

2. **Audio processing fails**:
   - Verify audio file format is supported
   - Check file size (max 50MB)
   - Ensure FFmpeg is installed

3. **Memory issues**:
   - Reduce quality setting
   - Use smaller audio files
   - Increase server RAM

### Logs

Check application logs:
```bash
# Docker
docker-compose logs audio-extraction-api

# Local
tail -f logs/app.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project uses open-source ML models and libraries. Please check individual licenses:
- Spleeter: MIT License
- FastAPI: MIT License
- Librosa: ISC License

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Open an issue on GitHub 