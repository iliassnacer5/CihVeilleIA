import httpx
import asyncio

async def verify_login():
    url = "http://localhost:8000/token"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=data)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ Login successful!")
                print(f"Token: {response.json().get('access_token')[:20]}...")
            else:
                print(f"❌ Login failed: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_login())
