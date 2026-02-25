# AI-Powered QA Test Automation Platform - Phase 1

## 🎯 Overview

This is a complete **Phase 1 implementation** of an AI-powered QA test automation platform that replaces traditional Selenium-based UI testing with intelligent AI agents. The system uses Playwright for browser automation, LLM-powered vision for element detection, and self-healing mechanisms to handle UI changes.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│   - Dashboard, Execute, Reports, Blueprints, Profile        │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API + SSE
┌─────────────────────┴───────────────────────────────────────┐
│                    FastAPI Backend (Python)                  │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Routers   │  │  Playwright  │  │   LLM Service     │  │
│  │ /api/runs  │  │   Engine     │  │  (Vision & RCA)   │  │
│  │ /api/flows │  │  (Browser    │  │                   │  │
│  │ /api/secrets│  │  Automation) │  │                   │  │
│  └────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼────┐  ┌───▼────┐  ┌───▼──────┐
    │PostgreSQL│  │ Redis  │  │ ChromaDB │
    │ (State)  │  │(Queue) │  │ (Vector) │
    └──────────┘  └────────┘  └──────────┘
```

## 📦 Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Playwright** - Browser automation (NOT Selenium)
- **PostgreSQL** - Persistent data storage
- **Redis** - Context store, pub-sub, Celery broker
- **Celery** - Background task execution
- **ChromaDB** - Vector search for flows
- **SQLAlchemy** - ORM for database operations
- **Groq/OpenAI (via Emergent LLM)** - Vision & reasoning

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Framer Motion** - Animations

## 🚀 Features Implemented (Phase 1)

### ✅ Core Backend Infrastructure
1. **FastAPI Application** with routers
2. **Playwright Automation Engine** with all primitives
3. **Flow Template System** (3 pre-built flows)
4. **Context Store** (Redis-backed)
5. **LLM Integration** (Vision + RCA)
6. **Database Models** (TestRun, StepLog, RCAReport, etc.)
7. **Celery Background Tasks**
8. **Docker Infrastructure**

For full details, see [Complete Documentation](#).

## 🔧 Quick Start

### Option 1: Docker Compose (Recommended)
```bash
cd /app
docker-compose up --build
```

### Option 2: Local Development
```bash
# Install dependencies
cd /app/backend
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
playwright install chromium

# Initialize database
python /app/init_db.py

# Start services
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
celery -A tasks.celery_app worker --loglevel=info
```

## 📋 API Endpoints

- `POST /api/runs` - Start test run
- `GET /api/runs/{run_id}/status` - Get status
- `GET /api/runs/{run_id}/stream` - SSE logs
- `GET /api/flows` - List flows
- `POST /api/secrets` - Manage test environments

API Docs: http://localhost:8001/docs

## ✅ Phase 1 Complete

**All core components implemented and ready for testing!**
