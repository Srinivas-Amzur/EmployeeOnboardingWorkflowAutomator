"""Quick script to list existing users from the DB."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT email, role, is_active FROM users ORDER BY created_at"))
        rows = result.all()
        print(f"{'EMAIL':<40} {'ROLE':<15} ACTIVE")
        print("-" * 65)
        for row in rows:
            print(f"{row[0]:<40} {row[1]:<15} {row[2]}")

asyncio.run(main())
