import asyncio
import httpx
import sys

async def verify_overhaul():
    url = "http://localhost:8000/token"
    # Authentification Admin
    data = {"username": "admin", "password": "cih2026"}
    
    async with httpx.AsyncClient() as client:
        print("🔐 Connexion en tant qu'admin...")
        resp = await client.post(url, data=data)
        if resp.status_code != 200:
            print(f"❌ Erreur login: {resp.text}")
            return
            
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: AMMC (Communiqués Marocains)
        source_id = "ammc_news"
        print(f"\n🚀 Test Scraping Source: {source_id}...")
        resp = await client.get(f"http://localhost:8000/sources/scrape/{source_id}", headers=headers, timeout=120)
        print(f"Résultat {source_id}: {resp.json()}")

        # Test 2: BIS (International)
        source_id = "bis_press"
        print(f"\n🚀 Test Scraping Source: {source_id}...")
        resp = await client.get(f"http://localhost:8000/sources/scrape/{source_id}", headers=headers, timeout=120)
        print(f"Résultat {source_id}: {resp.json()}")

        # Vérification des documents en DB
        print("\n🔍 Vérification des documents en base de données...")
        resp = await client.get("http://localhost:8000/documents", headers=headers)
        docs = resp.json()
        print(f"Nombre total de documents récupérés: {len(docs)}")
        
        if docs:
            print("\nDétails du premier document:")
            first6 = {k: docs[0].get(k) for k in ["title", "source_id", "category", "doc_type", "url"]}
            for k, v in first6.items():
                print(f" - {k}: {v}")

if __name__ == "__main__":
    asyncio.run(verify_overhaul())
