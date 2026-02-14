from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.backend.schemas import User, UserCreate, UserUpdate
from app.backend.auth import get_current_admin
from app.services.user_service import UserService
from app.services.exceptions import UserNotFoundException, DuplicateUserException, UnauthorizedActionException

router = APIRouter(prefix="/admin/users", tags=["admin_users"])

def get_user_service():
    return UserService()

@router.get("", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    filters = {
        "search": search,
        "role": role,
        "is_active": is_active
    }
    return await user_service.list_users(skip, limit, filters)

@router.post("", response_model=User)
async def create_user(
    payload: UserCreate,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        user_id = await user_service.create_user(
            user_data=payload.model_dump(),
            admin_id=current_admin["id"],
            admin_username=current_admin["username"],
            admin_role=current_admin["role"],
            ip=request.client.host
        )
        # Fetch created user to return
        user_dict = await user_service.repository.get_by_id(user_id)
        return user_dict
    except DuplicateUserException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{username}", response_model=User)
async def update_user(
    username: str,
    payload: UserUpdate,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        update_data = payload.model_dump(exclude_unset=True)
        await user_service.update_user(
            username=username,
            update_data=update_data,
            admin_id=current_admin["id"],
            admin_username=current_admin["username"],
            admin_role=current_admin["role"],
            ip=request.client.host
        )
        return await user_service.repository.get_by_username(username)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateUserException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{username}")
async def delete_user(
    username: str,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        await user_service.delete_user(
            username=username,
            admin_id=current_admin["id"],
            admin_username=current_admin["username"],
            admin_role=current_admin["role"],
            ip=request.client.host
        )
        return {"status": "success", "message": f"User {username} soft-deleted."}
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedActionException as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{username}/reset-password")
async def reset_password(
    username: str,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        new_password = await user_service.reset_password_token(
            username=username,
            admin_id=current_admin["id"],
            admin_username=current_admin["username"],
            admin_role=current_admin["role"],
            ip=request.client.host
        )
        return {"username": username, "new_password": new_password}
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
