from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import io
import csv

from app.backend.schemas import AuditLog
from app.backend.auth import get_current_admin
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])

def get_audit_service():
    return AuditService()

@router.get("/logs", response_model=List[AuditLog])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[float] = None,
    end_date: Optional[float] = None,
    audit_service: AuditService = Depends(get_audit_service),
    current_admin: dict = Depends(get_current_admin)
):
    filters = {
        "search": search,
        "action": action,
        "status": status,
        "start_date": start_date,
        "end_date": end_date
    }
    return await audit_service.get_filtered_logs(skip, limit, filters)

@router.get("/export")
async def export_audit_logs(
    audit_service: AuditService = Depends(get_audit_service),
    current_admin: dict = Depends(get_current_admin)
):
    logs = await audit_service.get_filtered_logs(limit=1000) # Export last 1000
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Timestamp", "Username", "Role", "Action", "Module", "Entity", "EntityID", "Status", "IP", "Details"])
    
    for log in logs:
        ts = datetime.fromtimestamp(log.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([
            ts,
            log.get("username"),
            log.get("role"),
            log.get("action"),
            log.get("module"),
            log.get("entity"),
            log.get("entity_id"),
            log.get("status"),
            log.get("ip_address"),
            str(log.get("details", {}))
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )
