#!/usr/bin/env python3
"""
Database initialization script
Creates all tables and optionally seeds initial data
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from models import init_db, SessionLocal, TestEnvironment, FlowTemplate
from core.flow_registry import flow_registry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize database and optionally seed data"""
    
    logger.info("Initializing database tables...")
    init_db()
    logger.info("✓ Database tables created successfully")
    
    # Seed flow templates from JSON files into database
    logger.info("Loading flow templates...")
    flow_registry.load_all_flows()
    
    db = SessionLocal()
    try:
        for flow_id, flow_data in flow_registry.flows.items():
            existing = db.query(FlowTemplate).filter(FlowTemplate.id == flow_id).first()
            if not existing:
                db_flow = FlowTemplate(
                    id=flow_data['id'],
                    name=flow_data['name'],
                    category=flow_data.get('category', 'general'),
                    description=flow_data.get('description', ''),
                    template_json=flow_data,
                    estimated_duration_seconds=flow_data.get('estimated_duration_seconds', 60),
                    is_active=True
                )
                db.add(db_flow)
                logger.info(f"  ✓ Added flow: {flow_data['name']}")
        
        db.commit()
        logger.info(f"✓ Loaded {len(flow_registry.flows)} flow templates")
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()
    
    logger.info("\n✅ Database initialization complete!")
    logger.info("\nYou can now start the application:")
    logger.info("  1. Start FastAPI: uvicorn backend.server:app --host 0.0.0.0 --port 8001")
    logger.info("  2. Start Celery: celery -A backend.tasks.celery_app worker --loglevel=info")
    logger.info("\nOr use Docker Compose:")
    logger.info("  docker-compose up")

if __name__ == "__main__":
    main()
