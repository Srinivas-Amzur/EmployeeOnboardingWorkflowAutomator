#!/usr/bin/env python3
"""Validation script for all components."""

import asyncio
import sys
from pathlib import Path

def test_imports():
    """Test all critical imports."""
    print("\n📦 TESTING IMPORTS...")
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        import langchain
        import chromadb
        print(f"   ✅ FastAPI {fastapi.__version__}")
        print(f"   ✅ SQLAlchemy {sqlalchemy.__version__}")
        print(f"   ✅ Pydantic {pydantic.__version__}")
        print(f"   ✅ LangChain {langchain.__version__}")
        print(f"   ✅ ChromaDB {chromadb.__version__}")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\n⚙️  TESTING CONFIGURATION...")
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"   ✅ Environment: {settings.ENVIRONMENT}")
        print(f"   ✅ Debug: {settings.DEBUG}")
        print(f"   ✅ Database configured: {bool(settings.DATABASE_URL)}")
        print(f"   ✅ ChromaDB host: {settings.CHROMADB_HOST}")
        return True
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return False

async def test_database():
    """Test database connection."""
    print("\n🗄️  TESTING DATABASE CONNECTION...")
    try:
        from app.db.session import engine
        from sqlalchemy import text
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as connection_test"))
            value = result.scalar()
            if value == 1:
                print("   ✅ Database: Connected to PostgreSQL")
                # Get version
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"   ✅ Database: {version[:60]}...")
                return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {str(e)[:100]}")
        return False

def test_models():
    """Test model imports."""
    print("\n📋 TESTING MODELS...")
    try:
        from app.models.user import User
        from app.models.employee import Employee
        from app.models.onboarding import OnboardingWorkflow
        from app.models.task import OnboardingTask
        print("   ✅ User model")
        print("   ✅ Employee model")
        print("   ✅ OnboardingWorkflow model")
        print("   ✅ OnboardingTask model")
        return True
    except Exception as e:
        print(f"   ❌ Model import failed: {e}")
        return False

def test_services():
    """Test service imports."""
    print("\n🔧 TESTING SERVICES...")
    try:
        from app.services.onboarding import OnboardingService
        from app.services.employee import EmployeeService
        from app.services.notification import NotificationService
        from app.services.document import DocumentService
        print("   ✅ OnboardingService")
        print("   ✅ EmployeeService")
        print("   ✅ NotificationService")
        print("   ✅ DocumentService")
        return True
    except Exception as e:
        print(f"   ❌ Service import failed: {e}")
        return False

def test_app():
    """Test FastAPI app creation."""
    print("\n🚀 TESTING FASTAPI APPLICATION...")
    try:
        from app.main import app
        from fastapi import FastAPI
        
        if isinstance(app, FastAPI):
            routes = len(app.routes)
            print(f"   ✅ FastAPI app created with {routes} routes")
            
            # Check middleware
            middleware_count = len(app.user_middleware)
            print(f"   ✅ Middleware stack: {middleware_count} layers")
            return True
    except Exception as e:
        print(f"   ❌ FastAPI app failed: {e}")
        return False

async def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("🔍 COMPONENT VALIDATION SUITE")
    print("="*60)
    
    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Models": test_models(),
        "Services": test_services(),
        "FastAPI App": test_app(),
        "Database": await test_database(),
    }
    
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for component, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{status:10} {component}")
    
    print(f"\nTotal: {passed}/{total} components validated")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS GO! Application is ready to start.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} component(s) need attention.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
