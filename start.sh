#!/bin/bash

# UCIP Startup Script
echo "🌍 Starting Urban Carbon Intelligence Platform..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start infrastructure
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait a moment for services to start
echo "⏳ Waiting for services to initialize..."
sleep 5

# Check service status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🚀 UCIP Services are starting up!"
echo ""
echo "📍 Access URLs:"
echo "   🏥 API Health:      http://localhost:8000/health"
echo "   📚 API Docs:        http://localhost:8000/docs"
echo "   📊 Dashboard:       http://localhost:3000"
echo "   🤖 MLflow:          http://localhost:5001"
echo "   📦 MinIO Console:   http://localhost:9001"
echo "   📈 Prometheus:      http://localhost:9090"
echo "   📊 Grafana:         http://localhost:3001"
echo ""
echo "🔧 To start the API server:"
echo "   cd api && uvicorn main:app --reload --port 8000"
echo ""
echo "🎨 To start the dashboard:"
echo "   cd dashboard && npm run dev"
echo ""
echo "✨ UCIP is ready for the NittanyAI Challenge!"
