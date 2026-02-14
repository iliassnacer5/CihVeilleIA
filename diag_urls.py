import asyncio
import httpx
from app.scraping.sources_registry import SOURCES_REGISTRY

async def check_urls():
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0, verify=False) as client:
        for key, source in SOURCES_REGISTRY.items():
            url = source["base_url"]
            try:
                response = await client.get(url)
                print(f"[{key}] {url} -> {response.status_code}")
                if response.status_code != 200:
                    print(f"  FAILED: {response.url}")
            except Exception as e:
                print(f"[{key}] {url} -> ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_urls())
