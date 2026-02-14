"""
Script d'initialisation de la base de données.
Crée le premier utilisateur admin pour accéder à la plateforme.

Usage:
    python init_db.py
"""

import asyncio
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.storage.mongo_store import MongoUserStore
from app.backend.auth import get_password_hash


async def create_admin_user():
    """Crée l'utilisateur administrateur par défaut."""
    store = MongoUserStore()
    await store.ensure_indexes()

    # Vérifier si l'admin existe déjà
    existing = await store.get_user_by_username("admin")
    if existing:
        print("✅ L'utilisateur admin existe déjà.")
        return

    admin_user = {
        "username": "admin",
        "email": "admin@cih.ma",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin",
        "is_active": True,
    }

    user_id = await store.create_user(admin_user)
    print(f"✅ Utilisateur admin créé avec succès (ID: {user_id})")
    print("   Username: admin")
    print("   Password: admin123")
    print("   ⚠️  Changez le mot de passe en production !")


async def main():
    print("🔧 Initialisation de la base de données CIH-Veille-IA...")
    print("=" * 50)
    await create_admin_user()
    print("=" * 50)
    print("🎉 Initialisation terminée.")


if __name__ == "__main__":
    asyncio.run(main())
