# YouTube Transcription API

A FastAPI-based server that provides transcription services for YouTube videos using two methods:
1. **YouTube Captions** - Fast extraction of existing captions/subtitles
2. **Whisper AI** - Speech-to-text transcription using OpenAI's Whisper model

## Features

- 🚀 **Dual transcription methods**: Captions (fast) + Whisper AI (accurate)
- 🔄 **Automatic fallback**: Uses captions when available, falls back to Whisper
- 🌍 **Language support**: Specify preferred caption language or auto-detect with Whisper
- 📝 **Structured output**: Timestamped transcript segments with metadata
- 🛡️ **Error handling**: Comprehensive error handling and validation
- 📖 **API documentation**: Automatic OpenAPI/Swagger documentation
- 🧹 **Resource management**: Automatic cleanup of temporary files

## Installation

You can run this API in two ways: **Docker (Recommended)** or **Local Python**.

### 🐳 Option 1: Docker (Recommended)

**Prerequisites:**
- Docker and Docker Compose

**Quick Start:**
```bash
# Clone the repository
git clone <repository-url>
cd yt-transcript-api

# Run the setup script (handles everything automatically)
chmod +x docker-run.sh
./docker-run.sh
```

**Manual Docker Setup:**
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f yt-transcription-api

# Test the API
docker-compose exec yt-transcription-api python test_api.py
```

### 🐍 Option 2: Local Python

**Prerequisites:**
- Python 3.8+
- FFmpeg (required for audio processing)

**Install FFmpeg:**

**Windows:**
```bash
# Using chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Install Dependencies:**
```bash
# Clone or download this repository
git clone <repository-url>
cd yt-transcript-api

# Install Python dependencies
pip install -r requirements.txt
```

## Usage

### Start the Server

**With Docker:**
```bash
# If you used the setup script, it's already running!
# Otherwise:
docker-compose up -d
```

**With Local Python:**
```bash
python run_server.py
```

The server will start on `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### API Endpoints

#### 1. Transcribe by URL/ID (POST)

```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
       "language": "en",
       "use_whisper": false
     }'
```

#### 2. Transcribe by Video ID (GET)

```bash
curl "http://localhost:8000/transcribe/dQw4w9WgXcQ?language=en&use_whisper=false"
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | ✅ | YouTube URL or video ID |
| `language` | string | ❌ | Preferred caption language (e.g., 'en', 'es', 'fr') |
| `use_whisper` | boolean | ❌ | Force Whisper even if captions exist (default: false) |

### Response Format

```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "duration": 212.0,
  "language": "en",
  "source": "captions",
  "segments": [
    {
      "start": 0.0,
      "duration": 3.5,
      "text": "We're no strangers to love"
    },
    {
      "start": 3.5,
      "duration": 2.8,
      "text": "You know the rules and so do I"
    }
  ],
  "created_at": "2024-01-15T10:30:00"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `video_id` | string | YouTube video ID |
| `title` | string | Video title (if available) |
| `duration` | float | Video duration in seconds |
| `language` | string | Language of the transcript |
| `source` | string | Either "captions" or "whisper" |
| `segments` | array | Transcript segments with timestamps |
| `created_at` | datetime | When the transcript was generated |

## Examples

### Python Client Example

```python
import requests

# Transcribe using captions (fast)
response = requests.post("http://localhost:8000/transcribe", json={
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
})

if response.status_code == 200:
    data = response.json()
    print(f"Title: {data['title']}")
    print(f"Source: {data['source']}")
    
    for segment in data['segments']:
        print(f"{segment['start']:.2f}s: {segment['text']}")
else:
    print(f"Error: {response.json()}")
```

### JavaScript/Node.js Example

```javascript
const fetch = require('node-fetch');

async function transcribeVideo(videoUrl) {
    const response = await fetch('http://localhost:8000/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: videoUrl })
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log(`Title: ${data.title}`);
        console.log(`Source: ${data.source}`);
        
        data.segments.forEach(segment => {
            console.log(`${segment.start.toFixed(2)}s: ${segment.text}`);
        });
    } else {
        console.error('Error:', await response.json());
    }
}

transcribeVideo('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
```

## How It Works

### 1. Caption-based Transcription (Primary Method)
- Uses `youtube-transcript-api` to fetch existing captions
- Very fast (< 1 second)
- Works with auto-generated and manual captions
- Supports multiple languages

### 2. Whisper-based Transcription (Fallback)
- Downloads audio using `yt-dlp`
- Transcribes using OpenAI's Whisper model
- More accurate for unclear audio
- Takes longer (1-5 minutes depending on video length)
- Automatically cleans up temporary files

### Decision Flow

```
YouTube URL → Extract Video ID → Try Captions → Success? → Return Result
                                      ↓ No
                              Download Audio → Whisper → Return Result
```

## Error Handling

The API handles various error scenarios:

| Error | Status Code | Description |
|-------|-------------|-------------|
| Invalid URL | 400 | Malformed YouTube URL or video ID |
| Video Not Found | 404 | Video doesn't exist or is private |
| No Captions Available | 200* | Falls back to Whisper automatically |
| Audio Download Failed | 500 | Network issues or restricted video |
| Whisper Failed | 500 | Audio processing or transcription error |

*When captions aren't available, the API automatically tries Whisper instead of returning an error.

## Performance Considerations

### Caption Mode (Fast)
- ~1 second response time
- No local processing required
- Limited by YouTube's API rate limits

### Whisper Mode (Accurate but Slower)
- 1-5 minutes depending on video length
- Requires local GPU/CPU processing
- Uses temporary disk space
- Model loaded once and cached

### Optimization Tips

1. **Use captions when possible** - Set `use_whisper: false` (default)
2. **Model size** - Change Whisper model in code (`base` → `tiny` for speed, `large` for accuracy)
3. **Caching** - Consider implementing Redis caching for repeated requests
4. **Async processing** - For production, consider background job queues

## Configuration

### Whisper Model Configuration

**With Docker (Recommended):**
```bash
# Set in .env file
echo "WHISPER_MODEL=large" >> .env

# Or set directly when starting
WHISPER_MODEL=tiny docker-compose up -d
```

**With Local Python:**
```bash
# Set environment variable
export WHISPER_MODEL=large
python run_server.py

# Or set inline
WHISPER_MODEL=tiny python run_server.py
```

**Available Models:**
- Set `WHISPER_MODEL` to: `tiny`, `base`, `small`, `medium`, or `large`
- Invalid values will fall back to `base` with a warning

**Check Current Model:**
```bash
# View current configuration
curl http://localhost:8000/health

# Example response:
# {
#   "status": "healthy",
#   "whisper_model": "base",
#   "whisper_model_loaded": true
# }
```

### Model Comparison

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | 39 MB | Very Fast | Good | Quick transcription |
| `base` | 142 MB | Fast | Better | Balanced (default) |
| `small` | 466 MB | Medium | Good | Better accuracy |
| `medium` | 769 MB | Slow | Very Good | High accuracy |
| `large` | 1550 MB | Very Slow | Excellent | Best accuracy |

## Deployment

### 🐳 Docker (Recommended)

**Development:**
```bash
docker-compose up -d
```

**Production:**
```bash
# Remove development volume mounts first
# Edit docker-compose.yml and comment out volume mounts under the API service
docker-compose up -d
```

**Scaling:**
```bash
# Run multiple instances
docker-compose up -d --scale yt-transcription-api=3
```

### 🐍 Local Python

**Development:**
```bash
python run_server.py
```

**Production with Uvicorn:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 🚀 Cloud Deployment

**Docker Hub:**
```bash
# Build and tag
docker build -t your-username/yt-transcription-api .
docker push your-username/yt-transcription-api

# Deploy anywhere Docker is supported
```

**Using the included files:**
- `Dockerfile` - Production-ready container
- `docker-compose.yml` - Complete orchestration
- `docker-run.sh` - Easy setup script

## Troubleshooting

### Common Issues

#### Docker Issues

**1. Docker not installed**
```
Error: command not found: docker
```
Solution: Install Docker from https://docs.docker.com/get-docker/

**2. Permission denied (Linux)**
```
Error: permission denied while trying to connect to Docker daemon
```
Solution: Add user to docker group: `sudo usermod -aG docker $USER` (logout/login required)

**3. Port already in use**
```
Error: port is already allocated
```
Solution: Stop other services using port 8000 or change port in docker-compose.yml

**4. Container won't start**
```bash
# Check logs
docker-compose logs yt-transcription-api

# Rebuild if needed
docker-compose build --no-cache
docker-compose up -d
```

#### Local Python Issues

**1. FFmpeg not found**
```
Error: ffmpeg not found
```
Solution: Install FFmpeg (see installation section)

**2. Video download fails**
```
Error: Unable to download video
```
- Check if video is public and available
- Some videos may be geo-restricted
- Check your internet connection

**3. Whisper model download slow**
```
Loading Whisper model...
```
- First run downloads the model (~142MB for base)
- Subsequent runs use cached model
- Consider using `tiny` model for faster loading

**4. Memory issues with long videos**
```
Error: Out of memory
```
- Use smaller Whisper model (`tiny` or `small`)
- Consider splitting long videos
- Increase system RAM if possible

### Logs

**Docker:**
```bash
# View live logs
docker-compose logs -f yt-transcription-api

# View recent logs
docker-compose logs --tail=100 yt-transcription-api
```

**Local Python:**
Check console output for:
- Video processing status
- Model loading progress
- Error details
- Performance information

### Useful Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart API service
docker-compose restart yt-transcription-api

# View service status
docker-compose ps

# Access container shell
docker-compose exec yt-transcription-api bash

# Run tests inside container
docker-compose exec yt-transcription-api python test_api.py

# View resource usage
docker stats

# Clean up unused resources
docker system prune
```

## License

This project is open source. Please check the licenses of dependencies:
- youtube-transcript-api: MIT
- OpenAI Whisper: MIT
- FastAPI: MIT
- yt-dlp: Unlicense

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Open an issue on GitHub

---

**Note**: This API respects YouTube's terms of service. Use responsibly and ensure you have rights to transcribe the content you're processing.
