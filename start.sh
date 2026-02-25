#!/bin/bash

# Quick Start Script for QA Automation Platform
echo "🚀 QA Automation Platform - Quick Start"
echo "========================================"
echo ""

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
    DOCKER_AVAILABLE=true
else
    echo "❌ Docker not found"
    DOCKER_AVAILABLE=false
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose found"
    COMPOSE_AVAILABLE=true
else
    echo "❌ Docker Compose not found"
    COMPOSE_AVAILABLE=false
fi

echo ""
echo "Choose deployment method:"
echo "1) Docker Compose (Recommended - Everything in containers)"
echo "2) Local Development (Manual service management)"
echo "3) Just start PostgreSQL & Redis via Docker"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        if [ "$DOCKER_AVAILABLE" = true ] && [ "$COMPOSE_AVAILABLE" = true ]; then
            echo ""
            echo "🐳 Starting all services with Docker Compose..."
            cd /app
            docker-compose up --build -d
            echo ""
            echo "✅ All services started!"
            echo ""
            echo "Services available at:"
            echo "  - Frontend: http://localhost:3000"
            echo "  - Backend API: http://localhost:8001"
            echo "  - API Docs: http://localhost:8001/docs"
            echo "  - PostgreSQL: localhost:5432"
            echo "  - Redis: localhost:6379"
            echo "  - ChromaDB: localhost:8000"
            echo ""
            echo "View logs:"
            echo "  docker-compose logs -f"
            echo ""
            echo "Stop services:"
            echo "  docker-compose down"
        else
            echo "❌ Docker or Docker Compose not available. Please install them first."
            exit 1
        fi
        ;;
    
    2)
        echo ""
        echo "📦 Local Development Setup"
        echo ""
        
        # Start databases with Docker
        if [ "$DOCKER_AVAILABLE" = true ]; then
            echo "Starting PostgreSQL..."
            docker run -d --name qa_postgres \
                -p 5432:5432 \
                -e POSTGRES_USER=qa_user \
                -e POSTGRES_PASSWORD=qa_password \
                -e POSTGRES_DB=qa_automation \
                postgres:16-alpine
            
            echo "Starting Redis..."
            docker run -d --name qa_redis \
                -p 6379:6379 \
                redis:7-alpine
            
            echo "Starting ChromaDB..."
            docker run -d --name qa_chromadb \
                -p 8000:8000 \
                -e IS_PERSISTENT=TRUE \
                chromadb/chroma:latest
            
            echo "✅ Database services started"
        else
            echo "⚠️  Please start PostgreSQL, Redis, and ChromaDB manually"
        fi
        
        echo ""
        echo "Installing Python dependencies..."
        cd /app/backend
        pip install -r requirements.txt
        pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
        playwright install chromium
        
        echo ""
        echo "Initializing database..."
        cd /app
        python init_db.py
        
        echo ""
        echo "✅ Setup complete!"
        echo ""
        echo "Start the services:"
        echo "  Terminal 1: cd /app/backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
        echo "  Terminal 2: cd /app/backend && celery -A tasks.celery_app worker --loglevel=info"
        echo "  Terminal 3: cd /app/frontend && yarn install && yarn dev"
        ;;
    
    3)
        if [ "$DOCKER_AVAILABLE" = true ]; then
            echo ""
            echo "🐳 Starting PostgreSQL and Redis..."
            
            docker run -d --name qa_postgres \
                -p 5432:5432 \
                -e POSTGRES_USER=qa_user \
                -e POSTGRES_PASSWORD=qa_password \
                -e POSTGRES_DB=qa_automation \
                postgres:16-alpine
            
            docker run -d --name qa_redis \
                -p 6379:6379 \
                redis:7-alpine
            
            docker run -d --name qa_chromadb \
                -p 8000:8000 \
                -e IS_PERSISTENT=TRUE \
                chromadb/chroma:latest
            
            echo ""
            echo "✅ Services started!"
            echo "  - PostgreSQL: localhost:5432"
            echo "  - Redis: localhost:6379"
            echo "  - ChromaDB: localhost:8000"
            echo ""
            echo "Stop services:"
            echo "  docker stop qa_postgres qa_redis qa_chromadb"
            echo "  docker rm qa_postgres qa_redis qa_chromadb"
        else
            echo "❌ Docker not available"
            exit 1
        fi
        ;;
    
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Setup complete! Check the logs for any errors."
echo "📚 Documentation: /app/DOCUMENTATION.md"
echo "🔗 API Docs: http://localhost:8001/docs"
