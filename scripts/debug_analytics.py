import asyncio, sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def main():
    from app.db.session import AsyncSessionLocal
    from app.services.analytics import AnalyticsService
    async with AsyncSessionLocal() as db:
        svc = AnalyticsService(db)
        try:
            result = await svc.get_dashboard_stats()
            import json
            print(json.dumps(result, default=str, indent=2))
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()

asyncio.run(main())
