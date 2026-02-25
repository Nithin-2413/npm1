# QA Automation Backend

## Structure

```
backend/
├── server.py              # Main FastAPI application
├── models.py              # SQLAlchemy database models
├── tasks.py               # Celery background tasks
├── celery_config.py       # Celery configuration
├── routers/              # API route handlers
│   ├── runs.py           # Test run endpoints
│   ├── flows.py          # Flow template endpoints
│   └── secrets.py        # Test environment secrets
├── core/                 # Core business logic
│   ├── playwright_engine.py  # Browser automation
│   ├── context_store.py     # Redis-backed state
│   ├── flow_registry.py     # Flow template manager
│   └── llm_service.py       # LLM integration
└── requirements.txt      # Python dependencies
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Set up environment variables in `.env`

4. Initialize database:
```python
from models import init_db
init_db()
```

5. Run the server:
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

6. Start Celery worker:
```bash
celery -A tasks.celery_app worker --loglevel=info
```