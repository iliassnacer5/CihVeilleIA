import asyncio
import httpx
import time

API_BASE_URL = "http://localhost:8000"

async def test_deletion():
    print("Testing Document Deletion...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login to get token
        print("Logging in...")
        try:
            resp = await client.post(f"{API_BASE_URL}/token", data={"username": "admin", "password": "cih2026"})
            resp.raise_for_status()
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✓ Login successful")
        except Exception as e:
            print(f"✗ Login failed: {e}")
            return

        # 2. Get documents
        print("Fetching documents...")
        resp = await client.get(f"{API_BASE_URL}/documents", headers=headers)
        docs = resp.json()
        if not docs:
            print("! No documents found to test deletion. Please run a scrape first.")
            return
        
        doc_id = docs[0]["id"]
        print(f"Found {len(docs)} documents. Testing deletion of ID: {doc_id}")

        # 3. Test single deletion
        print(f"Deleting single document: {doc_id}...")
        resp = await client.delete(f"{API_BASE_URL}/documents/{doc_id}", headers=headers)
        if resp.status_code == 200:
            print("✓ Single deletion successful")
        else:
            print(f"✗ Single deletion failed: {resp.status_code} {resp.text}")

        # 4. Test bulk deletion
        if len(docs) > 2:
            bulk_ids = [docs[1]["id"], docs[2]["id"]]
            print(f"Testing bulk deletion of IDs: {bulk_ids}...")
            resp = await client.post(f"{API_BASE_URL}/documents/bulk-delete", headers=headers, json={"doc_ids": bulk_ids})
            if resp.status_code == 200:
                print(f"✓ Bulk deletion successful: {resp.json()}")
            else:
                print(f"✗ Bulk deletion failed: {resp.status_code} {resp.text}")
        else:
            print("! Not enough documents for bulk deletion test.")

if __name__ == "__main__":
    asyncio.run(test_deletion())
