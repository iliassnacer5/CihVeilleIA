import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_source_flow():
    print("1. Testing GET /sources (initial)...")
    resp = requests.get(f"{BASE_URL}/sources")
    print(f"Status: {resp.status_code}, Sources count: {len(resp.json())}")

    print("\n2. Testing POST /sources (adding persistent source)...")
    new_source = {
        "name": "Audit Test Source",
        "url": "https://www.bankalmaghrib.ma/Actualites",
        "type": "Regulatory",
        "frequency": "Daily"
    }
    resp = requests.post(f"{BASE_URL}/sources", json=new_source)
    if resp.status_code == 200:
        source_data = resp.json()
        source_id = source_data['id']
        print(f"Success! Source ID: {source_id}")
    else:
        print(f"Failed to add source: {resp.text}")
        return

    print("\n3. Testing GET /sources (persistence check)...")
    resp = requests.get(f"{BASE_URL}/sources")
    sources = resp.json()
    found = any(s['id'] == source_id for s in sources)
    print(f"Source found in list: {found}")

    print(f"\n4. Testing GET /sources/scrape/{source_id} (manual scrape)...")
    # This might take a few seconds as it does real scraping
    start_time = time.time()
    resp = requests.get(f"{BASE_URL}/sources/scrape/{source_id}")
    duration = time.time() - start_time
    if resp.status_code == 200:
        print(f"Success! Scrape result: {resp.json()}")
        print(f"Scrape duration: {duration:.2f}s")
    else:
        print(f"Scrape failed: {resp.text}")

if __name__ == "__main__":
    try:
        test_source_flow()
    except Exception as e:
        print(f"Exception during test: {e}")
