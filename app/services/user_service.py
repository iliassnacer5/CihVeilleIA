import logging
import secrets
import string
from typing import List, Optional, Dict, Any
from passlib.context import CryptContext

from app.storage.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.exceptions import UserNotFoundException, DuplicateUserException, UnauthorizedActionException

logger = logging.getLogger(__name__)

# Use BCrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(
        self, 
        repository: Optional[UserRepository] = None, 
        audit_service: Optional[AuditService] = None
    ):
        self.repository = repository or UserRepository()
        self.audit_service = audit_service or AuditService()

    def _get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, user_data: Dict[str, Any], admin_id: str, admin_username: str, admin_role: str, ip: str) -> str:
        # Check uniqueness
        if await self.repository.get_by_username(user_data["username"], include_deleted=True):
            raise DuplicateUserException("username", user_data["username"])
        if await self.repository.get_by_email(user_data["email"], include_deleted=True):
            raise DuplicateUserException("email", user_data["email"])

        # Hash password
        user_data["hashed_password"] = self._get_password_hash(user_data.pop("password"))
        
        user_id = await self.repository.create(user_data)
        
        await self.audit_service.log_event(
            user_id=admin_id,
            username=admin_username,
            role=admin_role,
            action="CREATE_USER",
            module="USER_MGMT",
            entity="User",
            entity_id=user_id,
            details={"target_user": user_data["username"], "role": user_data["role"]},
            ip_address=ip
        )
        return user_id

    async def update_user(self, username: str, update_data: Dict[str, Any], admin_id: str, admin_username: str, admin_role: str, ip: str) -> bool:
        user = await self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException(username)

        if "password" in update_data:
            update_data["hashed_password"] = self._get_password_hash(update_data.pop("password"))

        # If email is changing, check uniqueness
        if "email" in update_data and update_data["email"] != user["email"]:
            if await self.repository.get_by_email(update_data["email"]):
                raise DuplicateUserException("email", update_data["email"])

        success = await self.repository.update(username, update_data)
        
        if success:
            await self.audit_service.log_event(
                user_id=admin_id,
                username=admin_username,
                role=admin_role,
                action="UPDATE_USER",
                module="USER_MGMT",
                entity="User",
                entity_id=user["id"],
                details={"target_user": username, "updates": list(update_data.keys())},
                ip_address=ip
            )
        return success

    async def delete_user(self, username: str, admin_id: str, admin_username: str, admin_role: str, ip: str) -> bool:
        if username == admin_username:
            raise UnauthorizedActionException("You cannot delete your own administrator account.")

        user = await self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException(username)

        success = await self.repository.soft_delete(username)
        
        if success:
            await self.audit_service.log_event(
                user_id=admin_id,
                username=admin_username,
                role=admin_role,
                action="DELETE_USER",
                module="USER_MGMT",
                entity="User",
                entity_id=user["id"],
                details={"target_user": username, "status": "soft_deleted"},
                ip_address=ip
            )
        return success

    async def reset_password_token(self, username: str, admin_id: str, admin_username: str, admin_role: str, ip: str) -> str:
        user = await self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException(username)

        # Generate a secure random password for now (as a 'reset')
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        hashed = self._get_password_hash(new_password)
        await self.repository.update(username, {"hashed_password": hashed})
        
        await self.audit_service.log_event(
            user_id=admin_id,
            username=admin_username,
            role=admin_role,
            action="RESET_PASSWORD",
            module="USER_MGMT",
            entity="User",
            entity_id=user["id"],
            details={"target_user": username},
            ip_address=ip
        )
        return new_password

    async def list_users(self, skip: int = 0, limit: int = 50, filters: Dict[str, Any] = None):
        return await self.repository.list_users(skip, limit, filters)

    async def get_user_count(self, filters: Dict[str, Any] = None):
        return await self.repository.count_users(filters)
