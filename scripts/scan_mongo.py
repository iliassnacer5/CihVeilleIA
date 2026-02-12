import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def scan_mongo():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    dbs = await client.list_database_names()
    print(f"Databases: {dbs}")
    
    for db_name in dbs:
        if db_name in ['admin', 'local', 'config']: continue
        db = client[db_name]
        collections = await db.list_collection_names()
        print(f"\nDatabase: {db_name}")
        for coll_name in collections:
            count = await db[coll_name].count_documents({})
            print(f"  - Collection: {coll_name} -> {count} docs")
            if count > 0 and 'doc' in coll_name:
                sample = await db[coll_name].find_one()
                print(f"    Sample Title: {sample.get('title')}")

if __name__ == "__main__":
    asyncio.run(scan_mongo())
