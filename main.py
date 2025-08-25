from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import os
import tempfile
import re
import logging
from datetime import datetime

# Import the transcription modules
from youtube_transcript_api import YouTubeTranscriptApi
import whisper
import yt_dlp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Transcription API",
    description="API for extracting transcripts from YouTube videos using captions or Whisper AI",
    version="1.0.0"
)

# Pydantic models
class TranscriptRequest(BaseModel):
    url: str
    language: Optional[str] = None
    use_whisper: Optional[bool] = False

class TranscriptSegment(BaseModel):
    start: float
    duration: float
    text: str

class TranscriptResponse(BaseModel):
    video_id: str
    title: Optional[str] = None
    duration: Optional[float] = None
    language: Optional[str] = None
    source: str  # "captions" or "whisper"
    segments: List[TranscriptSegment]
    created_at: datetime

class ErrorResponse(BaseModel):
    error: str
    message: str
    video_id: Optional[str] = None

# Global Whisper model (loaded once for efficiency)
whisper_model = None

def load_whisper_model():
    """Load Whisper model lazily"""
    global whisper_model
    if whisper_model is None:
        # Get model size from environment variable, default to "base"
        model_size = os.getenv("WHISPER_MODEL", "base").lower()
        
        # Validate model size
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if model_size not in valid_models:
            logger.warning(f"Invalid WHISPER_MODEL '{model_size}'. Using 'base' instead.")
            logger.info(f"Valid models: {', '.join(valid_models)}")
            model_size = "base"
        
        logger.info(f"Loading Whisper model: {model_size}")
        whisper_model = whisper.load_model(model_size)
        logger.info(f"Whisper model '{model_size}' loaded successfully")
    return whisper_model

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume the input is already a video ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    raise ValueError(f"Invalid YouTube URL or video ID: {url}")

def get_video_info(video_id: str) -> Dict[str, Any]:
    """Get basic video information using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'description': info.get('description'),
            }
    except Exception as e:
        logger.warning(f"Could not extract video info for {video_id}: {e}")
        return {}

def get_transcript_from_captions(video_id: str, language: Optional[str] = None) -> List[TranscriptSegment]:
    """Try to get transcript from existing YouTube captions"""
    try:
        if language:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript([language])
            transcript_data = transcript.fetch()
        else:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        
        segments = []
        for entry in transcript_data:
            segments.append(TranscriptSegment(
                start=entry['start'],
                duration=entry.get('duration', 0),
                text=entry['text']
            ))
        
        return segments
    
    except Exception as e:
        logger.info(f"Could not get captions for {video_id}: {e}")
        raise

def download_audio(video_id: str) -> str:
    """Download audio from YouTube video"""
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, f"{video_id}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'extractaudio': True,
        'audioformat': 'wav',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        
        # Find the downloaded file
        for file in os.listdir(temp_dir):
            if file.startswith(video_id) and file.endswith('.wav'):
                return os.path.join(temp_dir, file)
        
        raise Exception("Audio file not found after download")
    
    except Exception as e:
        logger.error(f"Failed to download audio for {video_id}: {e}")
        raise

def transcribe_with_whisper(audio_path: str) -> List[TranscriptSegment]:
    """Transcribe audio using Whisper"""
    model = load_whisper_model()
    
    try:
        result = model.transcribe(audio_path)
        segments = []
        
        for segment in result['segments']:
            segments.append(TranscriptSegment(
                start=segment['start'],
                duration=segment['end'] - segment['start'],
                text=segment['text'].strip()
            ))
        
        return segments
    
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise

def cleanup_temp_file(file_path: str):
    """Clean up temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            # Also remove the directory if it's empty
            temp_dir = os.path.dirname(file_path)
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
    except Exception as e:
        logger.warning(f"Could not clean up temp file {file_path}: {e}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "YouTube Transcription API",
        "version": "1.0.0",
        "endpoints": {
            "transcribe": "POST /transcribe - Transcribe a YouTube video",
            "health": "GET /health - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_size = os.getenv("WHISPER_MODEL", "base").lower()
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "whisper_model": model_size,
        "whisper_model_loaded": whisper_model is not None
    }

@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_video(request: TranscriptRequest, background_tasks: BackgroundTasks):
    """
    Transcribe a YouTube video using captions or Whisper AI
    
    - **url**: YouTube URL or video ID
    - **language**: Preferred language for captions (optional)
    - **use_whisper**: Force use of Whisper even if captions exist (optional)
    """
    try:
        # Extract video ID
        video_id = extract_video_id(request.url)
        logger.info(f"Processing video: {video_id}")
        
        # Get video information
        video_info = get_video_info(video_id)
        
        segments = []
        source = "captions"
        language_used = request.language
        
        # Try captions first (unless forced to use Whisper)
        if not request.use_whisper:
            try:
                segments = get_transcript_from_captions(video_id, request.language)
                logger.info(f"Successfully got captions for {video_id}")
            except Exception as e:
                logger.info(f"Captions not available for {video_id}, falling back to Whisper: {e}")
        
        # Fall back to Whisper if captions failed or were forced
        if not segments or request.use_whisper:
            logger.info(f"Using Whisper for transcription of {video_id}")
            
            # Download audio
            audio_path = download_audio(video_id)
            
            try:
                # Transcribe with Whisper
                segments = transcribe_with_whisper(audio_path)
                source = "whisper"
                language_used = "auto-detected"
                logger.info(f"Successfully transcribed {video_id} with Whisper")
                
            finally:
                # Schedule cleanup of temporary file
                background_tasks.add_task(cleanup_temp_file, audio_path)
        
        # Create response
        response = TranscriptResponse(
            video_id=video_id,
            title=video_info.get('title'),
            duration=video_info.get('duration'),
            language=language_used,
            source=source,
            segments=segments,
            created_at=datetime.now()
        )
        
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Transcription failed for {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

@app.get("/transcribe/{video_id}", response_model=TranscriptResponse)
async def transcribe_by_id(
    video_id: str,
    language: Optional[str] = None,
    use_whisper: Optional[bool] = False,
    background_tasks: BackgroundTasks = None
):
    """
    Transcribe a YouTube video by video ID
    
    - **video_id**: YouTube video ID
    - **language**: Preferred language for captions (optional)
    - **use_whisper**: Force use of Whisper even if captions exist (optional)
    """
    request = TranscriptRequest(
        url=video_id,
        language=language,
        use_whisper=use_whisper
    )
    return await transcribe_video(request, background_tasks)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
