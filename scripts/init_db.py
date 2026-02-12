import asyncio
import sys
import os

# Add the project root to sys.path to allow imports from app
sys.path.append(os.getcwd())

from app.storage.mongo_store import MongoUserStore
from app.backend.auth import get_password_hash
from app.config.logging_config import setup_logging

async def init_default_user():
    setup_logging()
    print("🚀 Initializing default user...")
    
    user_store = MongoUserStore()
    
    # Check if admin already exists
    existing_user = await user_store.get_user_by_username("admin")
    if existing_user:
        print("✅ User 'admin' already exists.")
        return

    # Create default admin user
    hashed_password = get_password_hash("cih2026") # Secure password for dev
    user_data = {
        "username": "admin",
        "email": "admin@cihbank.ma",
        "hashed_password": hashed_password,
        "role": "admin",
        "is_active": True
    }
    
    user_id = await user_store.create_user(user_data)
    print(f"🎉 Default user 'admin' created with ID: {user_id}")
    print("👉 Credentials: admin / cih2026")

if __name__ == "__main__":
    asyncio.run(init_default_user())
