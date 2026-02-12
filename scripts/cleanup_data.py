import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

async def cleanup_data():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    
    # 1. Nettoyage des documents enrichis
    print(f"🧹 Nettoyage de la collection {settings.mongodb_collection_enriched}...")
    result = await db[settings.mongodb_collection_enriched].delete_many({})
    print(f"✓ {result.deleted_count} documents supprimés.")
    
    # 2. Nettoyage des sources (si stockées en DB)
    coll_sources = "sources" # Hardcoded based on scan_mongo results
    print(f"🧹 Nettoyage de la collection {coll_sources}...")
    result = await db[coll_sources].delete_many({})
    print(f"✓ {result.deleted_count} sources supprimées.")

    # 3. Nettoyage des alertes (Optionnel mais recommandé pour un clean slate)
    coll_alerts = "alerts"
    print(f"🧹 Nettoyage de la collection {coll_alerts}...")
    result = await db[coll_alerts].delete_many({})
    print(f"✓ {result.deleted_count} alertes supprimées.")
    
    print("\n✅ Base de données nettoyée avec succès pour le nouveau périmètre du PFE.")

if __name__ == "__main__":
    asyncio.run(cleanup_data())
