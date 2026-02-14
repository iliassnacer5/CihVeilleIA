import asyncio
import aiohttp
import sys

API_URL = "http://127.0.0.1:8000"

async def debug_dashboard():
    print("--- Debugging Dashboard API ---")
    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("Logging in...")
        async with session.post(f"{API_URL}/token", data={"username": "admin", "password": "cih2026"}) as resp:
            if resp.status != 200:
                print(f"❌ Login Failed: {resp.status}")
                return
            token = (await resp.json())["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login Successful")

        # 2. Call Dashboard
        print("Calling /analytics/dashboard...")
        async with session.get(f"{API_URL}/analytics/dashboard", headers=headers) as resp:
            print(f"Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print("✅ Success! Data received.")
                print(data)
            else:
                print("❌ Error!")
                print(await resp.text())

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_dashboard())
