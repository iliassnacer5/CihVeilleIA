import asyncio
import aiohttp
import json
import websockets
import os
import sys

API_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/notifications/admin"

async def verify_alerts():
    print("--- Starting Alert Verification ---")

    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("\n[1] Logging in as admin...")
        try:
            async with session.post(f"{API_URL}/token", data={"username": "admin", "password": "cih2026"}) as resp:
                if resp.status != 200:
                    print(f"❌ Login Failed: {resp.status}")
                    return
                token = (await resp.json())["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                print("✅ Login Successful.")
        except Exception as e:
             print(f"❌ Login Error (Server might be down): {e}")
             return

        # 2. Connect WebSocket
        print(f"\n[2] Connecting to WebSocket: {WS_URL}")
        try:
            async with websockets.connect(WS_URL) as ws:
                print("✅ WebSocket Connected")
                
                # 3. Upload Document
                print("\n[3] Uploading Critical Document...")
                dummy_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT /F1 24 Tf 100 700 Td (Bank Al-Maghrib Sanction) Tj ET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000157 00000 n\n0000000302 00000 n\n0000000388 00000 n\ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n483\n%%EOF"
                
                data = aiohttp.FormData()
                data.add_field("file", dummy_pdf, filename="alert_test_critical.pdf", content_type="application/pdf")
                
                async with session.post(f"{API_URL}/documents/upload", data=data, headers=headers) as upload_resp:
                    if upload_resp.status == 200:
                        print("✅ Upload Successful")
                    else:
                        print(f"❌ Upload Failed: {upload_resp.status}")
                        return

                # 4. Listen for Alert
                print("\n[4] Waiting for Alert via WebSocket...")
                try:
                    # Expect "alive" or "new_document_alert"
                    received = False
                    start_time = asyncio.get_event_loop().time()
                    while (asyncio.get_event_loop().time() - start_time) < 10:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        payload = json.loads(msg)
                        
                        if payload.get("type") == "new_document_alert":
                            print("\n✅ ALERT RECEIVED!")
                            print(f"   Title: {payload['data']['title']}")
                            priority = payload['data']['priority']
                            print(f"   Priority: {priority}")
                            
                            if priority in ["critical", "high"]:
                                print("   ✅ Priority Logic CORRECT (Critical/High for 'Sanction')")
                            else:
                                print(f"   ⚠️ Priority Logic INCORRECT (Expected Critical/High, got {priority})")
                            received = True
                            break
                        elif payload.get("status") == "alive":
                            continue # Heartbeat
                        else:
                            print(f"   Ignoring message: {payload}")
                            
                    if not received:
                        print("❌ Timeout waiting for alert.")
                        
                except Exception as e:
                     print(f"❌ WebSocket Receive Error: {e}")

        except Exception as e:
            print(f"❌ WebSocket Connection Failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_alerts())
