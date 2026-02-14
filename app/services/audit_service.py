import logging
from typing import Any, Dict, Optional
from datetime import datetime
from app.storage.audit_repository import AuditRepository

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, repository: Optional[AuditRepository] = None):
        self.repository = repository or AuditRepository()

    async def log_event(
        self,
        user_id: str,
        username: str,
        role: str,
        action: str,
        module: str,
        entity: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """Centralized logging for all critical system actions."""
        log_entry = {
            "timestamp": datetime.utcnow().timestamp(),
            "user_id": user_id,
            "username": username,
            "role": role,
            "action": action,
            "module": module,
            "entity": entity,
            "entity_id": entity_id,
            "status": status,
            "details": details or {},
            "ip_address": ip_address or "0.0.0.0"
        }
        
        try:
            await self.repository.save_log(log_entry)
            logger.info(f"Audit Log: {action} by {username} on {module} - {status}")
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    async def get_filtered_logs(
        self, 
        skip: int = 0, 
        limit: int = 50, 
        filters: Optional[Dict[str, Any]] = None
    ):
        return await self.repository.list_logs(skip, limit, filters)

    async def get_total_count(self, filters: Optional[Dict[str, Any]] = None):
        return await self.repository.count_logs(filters)
