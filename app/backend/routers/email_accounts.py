from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from app.backend.auth import get_current_admin
from app.services.email_service import EmailConfigurationService
from app.storage.audit_log import audit_logger

router = APIRouter(prefix="/admin/emails", tags=["admin_email_management"])

class EmailAccountBase(BaseModel):
    email_address: EmailStr
    display_name: str
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    username: str
    enabled: bool = True
    is_default: bool = False

class EmailAccountCreate(EmailAccountBase):
    password: str

class EmailAccountUpdate(BaseModel):
    display_name: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None

class EmailAccountResponse(EmailAccountBase):
    id: str

def get_email_service():
    return EmailConfigurationService()

@router.get("", response_model=List[EmailAccountResponse])
async def list_email_accounts(
    service: EmailConfigurationService = Depends(get_email_service),
    current_admin: dict = Depends(get_current_admin)
):
    """Liste tous les comptes email configurés (sans les mots de passe)."""
    return await service.repository.list_accounts()

@router.post("", response_model=EmailAccountResponse)
async def create_email_account(
    payload: EmailAccountCreate,
    service: EmailConfigurationService = Depends(get_email_service),
    current_admin: dict = Depends(get_current_admin)
):
    """Crée un nouveau compte email."""
    account_id = await service.add_account(payload.model_dump(), current_admin["username"])
    
    await audit_logger.log_event(
        "EMAIL_ACCOUNT_CREATED", current_admin["username"], "SUCCESS",
        {"email": payload.email_address, "id": account_id}
    )
    
    account = await service.repository.get_by_id(account_id)
    return account

@router.patch("/{account_id}", response_model=bool)
async def update_email_account(
    account_id: str,
    payload: EmailAccountUpdate,
    service: EmailConfigurationService = Depends(get_email_service),
    current_admin: dict = Depends(get_current_admin)
):
    """Met à jour un compte email."""
    success = await service.update_account(account_id, payload.model_dump(exclude_unset=True))
    
    await audit_logger.log_event(
        "EMAIL_ACCOUNT_UPDATED", current_admin["username"], "SUCCESS" if success else "FAILED",
        {"id": account_id}
    )
    return success

@router.delete("/{account_id}")
async def delete_email_account(
    account_id: str,
    service: EmailConfigurationService = Depends(get_email_service),
    current_admin: dict = Depends(get_current_admin)
):
    """Supprime un compte email."""
    success = await service.repository.delete_account(account_id)
    
    await audit_logger.log_event(
        "EMAIL_ACCOUNT_DELETED", current_admin["username"], "SUCCESS" if success else "FAILED",
        {"id": account_id}
    )
    return {"status": "success" if success else "failed"}

@router.post("/{account_id}/test")
async def test_email_account(
    account_id: str,
    service: EmailConfigurationService = Depends(get_email_service),
    current_admin: dict = Depends(get_current_admin)
):
    """Teste la connexion SMTP d'un compte existant."""
    account = await service.repository.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
        
    success, message = await service.test_smtp_connection(account)
    
    await audit_logger.log_event(
        "SMTP_TEST_TRIGGERED", current_admin["username"], "SUCCESS" if success else "FAILED",
        {"id": account_id, "message": message}
    )
    
    return {"success": success, "message": message}

@router.post("/test-params")
async def test_email_params(
    payload: EmailAccountCreate,
    service: EmailConfigurationService = Depends(get_email_service),
    current_admin: dict = Depends(get_current_admin)
):
    """Teste les paramètres SMTP avant création."""
    success, message = await service.test_smtp_connection(payload.model_dump())
    return {"success": success, "message": message}
