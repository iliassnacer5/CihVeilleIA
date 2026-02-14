import asyncio
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage.mongo_client import get_db

async def inspect_admin():
    db = get_db()
    user = await db.users.find_one({"username": "admin"})
    if user:
        print(f"User found: {user['username']}")
        print(f"Hashed password in DB: {user.get('hashed_password')}")
        if user.get("hashed_password"):
            hp = user["hashed_password"]
            if hp.startswith("$2b$") or hp.startswith("$2a$"):
                print("Looks like a valid bcrypt hash.")
            else:
                print("⚠️ DOES NOT look like a valid bcrypt hash.")
    else:
        print("User 'admin' not found.")

if __name__ == "__main__":
    asyncio.run(inspect_admin())
