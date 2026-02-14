import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.storage.mongo_store import MongoUserStore
from app.backend.auth import get_password_hash

async def migrate():
    store = MongoUserStore()
    await store.ensure_indexes()
    
    # Update all users to ROLE_USER by default if they don't have a role or have 'analyst'
    await store.collection.update_many(
        {"role": {"$in": ["analyst", None]}},
        {"$set": {"role": "ROLE_USER", "is_active": True}}
    )
    
    # Update 'admin' user to ROLE_ADMIN
    await store.collection.update_many(
        {"username": "admin"},
        {"$set": {"role": "ROLE_ADMIN", "is_active": True}}
    )
    
    # If no admin exists, create one
    admin = await store.get_user_by_username("admin")
    if not admin:
        print("Creating default admin user...")
        await store.create_user({
            "username": "admin",
            "email": "admin@cih.ma",
            "hashed_password": get_password_hash("admin123"),
            "role": "ROLE_ADMIN",
            "is_active": True
        })
    else:
        print("Admin user already exists.")

    # If no regular user exists, create one
    user = await store.get_user_by_username("user_test")
    if not user:
        print("Creating default regular user...")
        await store.create_user({
            "username": "user_test",
            "email": "user@cih.ma",
            "hashed_password": get_password_hash("user123"),
            "role": "ROLE_USER",
            "is_active": True
        })
    else:
        print("Regular user already exists.")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
