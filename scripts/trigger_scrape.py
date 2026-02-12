import asyncio
import httpx

async def trigger_scrape():
    url = "http://localhost:8000/token"
    data = {"username": "admin", "password": "cih2026"}
    
    async with httpx.AsyncClient() as client:
        print("Logging in...")
        resp = await client.post(url, data=data)
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        source_id = "imf_news"
        print(f"Triggering scrape for {source_id}...")
        resp = await client.get(f"http://localhost:8000/sources/scrape/{source_id}", headers=headers, timeout=300)
        print(f"Scrape result: {resp.json()}")

if __name__ == "__main__":
    asyncio.run(trigger_scrape())
