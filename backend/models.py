from pymongo import MongoClient
from datetime import datetime, timezone
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "qa_automation")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
test_runs_collection = db["test_runs"]
step_logs_collection = db["step_logs"]
rca_reports_collection = db["rca_reports"]
test_environments_collection = db["test_environments"]
flow_templates_collection = db["flow_templates"]
schedules_collection = db["schedules"]

def get_db():
    """Get database instance"""
    return db

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

# Schema definitions for validation
TEST_RUN_SCHEMA = {
    "run_id": str,
    "flow_id": str,
    "flow_name": str,
    "status": str,  # pending, running, passed, failed, cancelled
    "started_at": datetime,
    "finished_at": datetime,
    "variables_used": dict,
    "order_id_captured": str,
    "test_env_id": str,
    "error_summary": str,
    "natural_language_input": str,
    "created_at": datetime,
    "updated_at": datetime,
}

STEP_LOG_SCHEMA = {
    "run_id": str,
    "step_number": int,
    "step_description": str,
    "action": str,
    "target": str,
    "value": str,
    "status": str,
    "screenshot_b64": str,
    "timestamp": datetime,
    "duration_ms": int,
    "error_message": str,
    "retry_count": int,
    "details": dict,
}

RCA_REPORT_SCHEMA = {
    "run_id": str,
    "error_summary": str,
    "root_cause": str,
    "affected_step": int,
    "network_errors": list,
    "console_errors": list,
    "ai_explanation": str,
    "suggested_fix": str,
    "confidence_score": float,
    "created_at": datetime,
}

TEST_ENVIRONMENT_SCHEMA = {
    "env_id": str,
    "test_env": str,
    "release_branch": str,
    "url": str,
    "username": str,
    "password": str,
    "created_at": datetime,
    "updated_at": datetime,
}

FLOW_TEMPLATE_SCHEMA = {
    "flow_id": str,
    "name": str,
    "category": str,
    "description": str,
    "template_json": dict,
    "estimated_duration_seconds": int,
    "created_at": datetime,
    "updated_at": datetime,
    "is_active": bool,
}

SCHEDULE_SCHEMA = {
    "schedule_id": str,
    "name": str,
    "flow_id": str,
    "cron_expression": str,
    "variables": dict,
    "test_env_id": str,
    "is_active": bool,
    "created_at": datetime,
    "last_run_at": datetime,
    "next_run_at": datetime,
    "total_runs": int,
}

def init_db():
    """Initialize database with indexes"""
    # Create indexes for better query performance
    test_runs_collection.create_index("run_id", unique=True)
    test_runs_collection.create_index("status")
    test_runs_collection.create_index("flow_id")
    test_runs_collection.create_index("created_at")
    
    step_logs_collection.create_index("run_id")
    step_logs_collection.create_index([("run_id", 1), ("step_number", 1)])
    
    rca_reports_collection.create_index("run_id")
    
    test_environments_collection.create_index("env_id", unique=True)
    
    flow_templates_collection.create_index("flow_id", unique=True)
    
    schedules_collection.create_index("schedule_id", unique=True)
    schedules_collection.create_index("is_active")
    
    print("Database indexes created successfully")

# Helper functions for CRUD operations
def create_test_run(data: dict) -> dict:
    """Create a new test run"""
    now = datetime.now(timezone.utc)
    doc = {
        "run_id": data.get("run_id"),
        "flow_id": data.get("flow_id"),
        "flow_name": data.get("flow_name", ""),
        "status": data.get("status", "pending"),
        "started_at": data.get("started_at", now),
        "finished_at": data.get("finished_at"),
        "variables_used": data.get("variables_used", {}),
        "order_id_captured": data.get("order_id_captured"),
        "test_env_id": data.get("test_env_id"),
        "error_summary": data.get("error_summary"),
        "natural_language_input": data.get("natural_language_input"),
        "created_at": now,
        "updated_at": now,
    }
    result = test_runs_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_test_run(run_id: str) -> dict:
    """Get a test run by run_id"""
    doc = test_runs_collection.find_one({"run_id": run_id})
    return serialize_doc(doc)

def update_test_run(run_id: str, updates: dict) -> dict:
    """Update a test run"""
    updates["updated_at"] = datetime.now(timezone.utc)
    test_runs_collection.update_one(
        {"run_id": run_id},
        {"$set": updates}
    )
    return get_test_run(run_id)

def create_step_log(data: dict) -> dict:
    """Create a step log entry"""
    doc = {
        "run_id": data.get("run_id"),
        "step_number": data.get("step_number"),
        "step_description": data.get("step_description"),
        "action": data.get("action"),
        "target": data.get("target"),
        "value": data.get("value"),
        "status": data.get("status", "pending"),
        "screenshot_b64": data.get("screenshot_b64"),
        "timestamp": datetime.now(timezone.utc),
        "duration_ms": data.get("duration_ms"),
        "error_message": data.get("error_message"),
        "retry_count": data.get("retry_count", 0),
        "details": data.get("details"),
    }
    result = step_logs_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_step_logs(run_id: str) -> list:
    """Get all step logs for a run"""
    docs = list(step_logs_collection.find({"run_id": run_id}).sort("step_number", 1))
    return serialize_doc(docs)

def create_rca_report(data: dict) -> dict:
    """Create an RCA report"""
    doc = {
        "run_id": data.get("run_id"),
        "error_summary": data.get("error_summary"),
        "root_cause": data.get("root_cause"),
        "affected_step": data.get("affected_step"),
        "network_errors": data.get("network_errors", []),
        "console_errors": data.get("console_errors", []),
        "ai_explanation": data.get("ai_explanation"),
        "suggested_fix": data.get("suggested_fix"),
        "confidence_score": data.get("confidence_score"),
        "created_at": datetime.now(timezone.utc),
    }
    result = rca_reports_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_rca_report(run_id: str) -> dict:
    """Get RCA report for a run"""
    doc = rca_reports_collection.find_one({"run_id": run_id})
    return serialize_doc(doc)

def create_test_environment(data: dict) -> dict:
    """Create a test environment"""
    now = datetime.now(timezone.utc)
    doc = {
        "env_id": data.get("env_id"),
        "test_env": data.get("test_env"),
        "release_branch": data.get("release_branch"),
        "url": data.get("url"),
        "username": data.get("username"),
        "password": data.get("password"),
        "created_at": now,
        "updated_at": now,
    }
    result = test_environments_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_test_environment(env_id: str) -> dict:
    """Get a test environment by env_id"""
    doc = test_environments_collection.find_one({"env_id": env_id})
    return serialize_doc(doc)

def list_test_environments() -> list:
    """List all test environments"""
    docs = list(test_environments_collection.find())
    return serialize_doc(docs)

def update_test_environment(env_id: str, updates: dict) -> dict:
    """Update a test environment"""
    updates["updated_at"] = datetime.now(timezone.utc)
    test_environments_collection.update_one(
        {"env_id": env_id},
        {"$set": updates}
    )
    return get_test_environment(env_id)

def delete_test_environment(env_id: str) -> bool:
    """Delete a test environment"""
    result = test_environments_collection.delete_one({"env_id": env_id})
    return result.deleted_count > 0
