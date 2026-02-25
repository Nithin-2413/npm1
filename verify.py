#!/usr/bin/env python3
"""
Verification script to check all Phase 1 components
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    if Path(dirpath).is_dir():
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description} missing: {dirpath}")
        return False

def main():
    """Run verification checks"""
    print("🔍 Phase 1 Verification Checklist")
    print("=" * 50)
    print()
    
    all_checks = []
    
    # 1. Backend Files
    print("📂 Backend Core Files:")
    all_checks.append(check_file_exists("/app/backend/server.py", "Main FastAPI app"))
    all_checks.append(check_file_exists("/app/backend/models.py", "Database models"))
    all_checks.append(check_file_exists("/app/backend/tasks.py", "Celery tasks"))
    all_checks.append(check_file_exists("/app/backend/celery_config.py", "Celery config"))
    all_checks.append(check_file_exists("/app/backend/requirements.txt", "Requirements"))
    all_checks.append(check_file_exists("/app/backend/Dockerfile", "Dockerfile"))
    all_checks.append(check_file_exists("/app/backend/.env", "Environment file"))
    print()
    
    # 2. Routers
    print("🛣️  API Routers:")
    all_checks.append(check_file_exists("/app/backend/routers/__init__.py", "Routers init"))
    all_checks.append(check_file_exists("/app/backend/routers/runs.py", "Runs router"))
    all_checks.append(check_file_exists("/app/backend/routers/flows.py", "Flows router"))
    all_checks.append(check_file_exists("/app/backend/routers/secrets.py", "Secrets router"))
    print()
    
    # 3. Core Components
    print("⚙️  Core Components (Phase 1):")
    all_checks.append(check_file_exists("/app/backend/core/__init__.py", "Core init"))
    all_checks.append(check_file_exists("/app/backend/core/playwright_engine.py", "Playwright engine"))
    all_checks.append(check_file_exists("/app/backend/core/context_store.py", "Context store"))
    all_checks.append(check_file_exists("/app/backend/core/flow_registry.py", "Flow registry"))
    all_checks.append(check_file_exists("/app/backend/core/llm_service.py", "LLM service (Phase 1)"))
    print()
    
    # 3b. Phase 2 LLM Components
    print("🧠 Phase 2 LLM Orchestration:")
    all_checks.append(check_directory_exists("/app/backend/core/llm", "LLM package"))
    all_checks.append(check_file_exists("/app/backend/core/llm/__init__.py", "LLM init"))
    all_checks.append(check_file_exists("/app/backend/core/llm/intent_parser.py", "Intent parser"))
    all_checks.append(check_file_exists("/app/backend/core/llm/flow_selector.py", "Flow selector"))
    all_checks.append(check_file_exists("/app/backend/core/llm/variable_resolver.py", "Variable resolver"))
    all_checks.append(check_file_exists("/app/backend/core/llm/step_builder.py", "Step builder"))
    print()
    
    # 4. Flow Templates
    print("📋 Flow Templates:")
    all_checks.append(check_directory_exists("/app/flows/templates", "Templates directory"))
    all_checks.append(check_file_exists("/app/flows/templates/login_customer_selection.json", "Login flow"))
    all_checks.append(check_file_exists("/app/flows/templates/create_order_single_tn.json", "Create order flow"))
    all_checks.append(check_file_exists("/app/flows/templates/cancel_order.json", "Cancel order flow"))
    print()
    
    # 5. Docker Files
    print("🐳 Docker Configuration:")
    all_checks.append(check_file_exists("/app/docker-compose.yml", "Docker Compose"))
    print()
    
    # 6. Scripts & Documentation
    print("📚 Scripts & Documentation:")
    all_checks.append(check_file_exists("/app/init_db.py", "Database init script"))
    all_checks.append(check_file_exists("/app/start.sh", "Quick start script"))
    all_checks.append(check_file_exists("/app/README.md", "Main README"))
    all_checks.append(check_file_exists("/app/DOCUMENTATION.md", "Phase 1 documentation"))
    all_checks.append(check_file_exists("/app/PHASE2_DOCUMENTATION.md", "Phase 2 documentation"))
    all_checks.append(check_file_exists("/app/image_testing.md", "Image testing guide"))
    print()
    
    # 7. Frontend
    print("🎨 Frontend:")
    all_checks.append(check_directory_exists("/app/frontend/src", "Frontend source"))
    all_checks.append(check_file_exists("/app/frontend/package.json", "Frontend package.json"))
    print()
    
    # Summary
    print("=" * 50)
    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total) * 100
    
    print(f"\n✨ Verification Results: {passed}/{total} checks passed ({percentage:.1f}%)")
    
    if passed == total:
        print("\n🎉 All components verified! Phase 1 is COMPLETE!")
        print("\n📖 Next Steps:")
        print("  1. Review DOCUMENTATION.md for detailed information")
        print("  2. Run: ./start.sh (or manually start services)")
        print("  3. Initialize database: python init_db.py")
        print("  4. Access API docs: http://localhost:8001/docs")
        print("  5. Start testing with your application!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} components missing. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
