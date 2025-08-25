#!/usr/bin/env python3
"""
Development server startup script for YouTube Transcription API
"""

import uvicorn
import sys
import os

def main():
    """Start the development server"""
    
    # Check if FFmpeg is available
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  FFmpeg not found. Audio transcription with Whisper will not work.")
        print("   Please install FFmpeg: https://ffmpeg.org/download.html")
    
    # Check dependencies
    try:
        import fastapi
        import youtube_transcript_api
        import whisper
        import yt_dlp
        print("✅ All dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n🚀 Starting YouTube Transcription API Server...")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/health")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

if __name__ == "__main__":
    main()
