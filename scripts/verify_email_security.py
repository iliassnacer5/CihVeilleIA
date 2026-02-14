import asyncio
import httpx
import json

async def verify_security():
    base_url = "http://localhost:8000"
    
    # login as admin to get token
    async with httpx.AsyncClient() as client:
        # Note: Assuming 'admin' / 'admin123' works based on previous steps/knowledge
        # If not, this is just a template for verification.
        login_resp = await client.post(f"{base_url}/token", data={"username": "admin", "password": "admin123"})
        if login_resp.status_code != 200:
            print(f"Login failed: {login_resp.text}")
            return
            
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Verify Listing doesn't return passwords
        list_resp = await client.get(f"{base_url}/admin/emails", headers=headers)
        print(f"List Accounts Status: {list_resp.status_code}")
        if list_resp.status_code == 200:
            accounts = list_resp.json()
            for acc in accounts:
                if "encrypted_password" in acc or "password" in acc:
                    print(f"CRITICAL SECURITY FAILURE: Password found in account {acc.get('id')}")
                else:
                    print(f"Account {acc.get('email_address')} verified: No password exposed.")
        
        # 2. Verify RBAC (Trying to access with a regular user token if possible)
        # For now, we mainly check that the admin can access.
        
if __name__ == "__main__":
    asyncio.run(verify_security())
