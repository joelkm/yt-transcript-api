#!/bin/bash

# Docker Compose startup script for YouTube Transcription API

echo "🐳 YouTube Transcription API - Docker Setup"
echo "=" * 50

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "✅ Created .env file. You can modify it if needed."
fi

# Create temp directory if it doesn't exist
if [ ! -d ./temp ]; then
    echo "📁 Creating temp directory..."
    mkdir -p ./temp
    echo "✅ Created temp directory for audio files."
fi

# Build and start the services
echo ""
echo "🔨 Building Docker image..."
if command -v docker-compose &> /dev/null; then
    docker-compose build
else
    docker compose build
fi

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker image build failed"
    exit 1
fi

echo ""
echo "🚀 Starting services..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

if [ $? -eq 0 ]; then
    echo "✅ Services started successfully"
    echo ""
    echo "🌐 API is now available at:"
    echo "   URL: http://localhost:8000"
    echo "   Docs: http://localhost:8000/docs"
    echo "   Health: http://localhost:8000/health"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose logs -f yt-transcription-api"
    echo "   Stop services: docker-compose down"
    echo "   Restart: docker-compose restart"
    echo "   Shell access: docker-compose exec yt-transcription-api bash"
    echo ""
    echo "🧪 Test the API:"
    echo "   docker-compose exec yt-transcription-api python test_api.py"
else
    echo "❌ Failed to start services"
    exit 1
fi
