#!/usr/bin/env python3
"""
Simple test script for the YouTube Transcription API
"""

import requests
import json
import sys
from typing import Dict, Any

API_BASE = "http://localhost:8000"

def test_health_check() -> bool:
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed")
            print(f"   Whisper model: {health_data.get('whisper_model', 'unknown')}")
            print(f"   Model loaded: {health_data.get('whisper_model_loaded', False)}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Is it running?")
        return False

def test_transcription(video_url: str, use_whisper: bool = False) -> Dict[str, Any]:
    """Test video transcription"""
    print(f"\n🎬 Testing transcription for: {video_url}")
    print(f"   Using Whisper: {use_whisper}")
    
    payload = {
        "url": video_url,
        "use_whisper": use_whisper
    }
    
    try:
        response = requests.post(f"{API_BASE}/transcribe", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Transcription successful!")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Duration: {data.get('duration', 'N/A')} seconds")
            print(f"   Source: {data['source']}")
            print(f"   Language: {data.get('language', 'N/A')}")
            print(f"   Segments: {len(data['segments'])}")
            
            # Show first few segments
            print("\n📝 First few segments:")
            for i, segment in enumerate(data['segments'][:3]):
                print(f"   {segment['start']:.1f}s: {segment['text'][:100]}...")
            
            return data
        else:
            error_data = response.json()
            print(f"❌ Transcription failed: {response.status_code}")
            print(f"   Error: {error_data}")
            return {}
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {}

def main():
    """Run tests"""
    print("🧪 YouTube Transcription API Test Suite")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("\n💀 Server is not healthy, aborting tests")
        sys.exit(1)
    
    # Test videos (these are short, public videos with captions)
    test_videos = [
        "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up (has captions)
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo" (short video)
    ]
    
    for video in test_videos:
        # Test with captions first
        result = test_transcription(video, use_whisper=False)
        
        if not result:
            print(f"⚠️  Captions failed for {video}, testing with Whisper...")
            test_transcription(video, use_whisper=True)
    
    print("\n" + "=" * 50)
    print("🎉 Tests completed!")
    print("\n💡 To run manual tests:")
    print(f"   curl -X POST {API_BASE}/transcribe -H 'Content-Type: application/json' -d '{{\"url\":\"dQw4w9WgXcQ\"}}'")
    print(f"   curl {API_BASE}/transcribe/dQw4w9WgXcQ")
    print(f"   Visit {API_BASE}/docs for interactive API docs")

if __name__ == "__main__":
    main()
