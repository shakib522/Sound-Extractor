#!/bin/bash

# Audio Extraction API Deployment Script

set -e

echo "🎵 Audio Extraction API Deployment Script"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads outputs logs

# Set permissions
chmod 755 uploads outputs logs

# Build and start the application
echo "🐳 Building and starting the application..."
docker-compose up --build -d

# Wait for the application to start
echo "⏳ Waiting for the application to start..."
sleep 30

# Check if the application is running
echo "🔍 Checking application health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
    echo "🌐 API is available at: http://localhost:8000"
    echo "📚 API documentation at: http://localhost:8000/docs"
    echo "🔧 Health check at: http://localhost:8000/health"
else
    echo "❌ Application failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test the API using the test_main.http file"
echo "2. Upload an audio file to test extraction"
echo "3. Check logs: docker-compose logs -f"
echo "4. Stop the service: docker-compose down" 