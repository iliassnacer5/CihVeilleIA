import pytest
from httpx import AsyncClient, ASGITransport
from app.backend.api import app
from app.backend.auth import create_access_token

@pytest.fixture(autouse=True)
def reset_singletons():
    import app.backend.api as api
    api._NLP_SERVICE = None
    api._RAG_PIPELINE = None
    api._RAG_CHATBOT = None
    if api._MONGO_CLIENT:
        api._MONGO_CLIENT.close()
    api._MONGO_CLIENT = None
    api._MONGO_STORE = None
    api._SOURCE_STORE = None
    api._SYSTEM_STORE = None
    api._ORCHESTRATOR = None
    api._USER_STORE = None
    api._ALERT_STORE = None
    api._CONNECTION_MANAGER = None
    yield

@pytest.mark.asyncio
async def test_admin_route_access():
    # Regular user token
    user_token = create_access_token(data={"sub": "user_test"})
    headers = {"Authorization": f"Bearer {user_token}"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Try to access admin users list
        response = await ac.get("/admin/users", headers=headers)
        if response.status_code != 403:
            print(f"DEBUG Response: {response.text}")
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_audit_logs_access():
    # Regular user token
    user_token = create_access_token(data={"sub": "user_test"})
    headers = {"Authorization": f"Bearer {user_token}"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Try to access audit logs
        response = await ac.get("/audit/logs", headers=headers)
        if response.status_code != 403:
            print(f"DEBUG Response: {response.text}")
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_access():
    # Admin user token (must ensure 'admin' exists in DB or mock it)
    # For integration test, we use the real DB so 'admin' should be there after migration
    admin_token = create_access_token(data={"sub": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/admin/users", headers=headers)
        if response.status_code != 200:
            print(f"DEBUG Response: {response.text}")
        assert response.status_code == 200
