# Create new file: src/api/routes/auth.py (Optional - for user info endpoints)

from fastapi import APIRouter, Depends
from typing import Dict, Any
from src.api.auth_dependencies import get_current_user, get_current_user_optional
from src.models.responses import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserInfoResponse(BaseModel):
    user_id: str
    email: str
    username: str
    groups: list
    authenticated: bool = True

@router.get("/me", response_model=UserInfoResponse)
async def get_my_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information from token"""
    return UserInfoResponse(
        user_id=current_user["user_id"],
        email=current_user.get("email", ""),
        username=current_user.get("username", ""),
        groups=current_user.get("groups", [])
    )

@router.get("/verify")
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Verify if the current token is valid"""
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "exp": current_user.get("exp")
    }

@router.get("/health")
async def auth_health_check(current_user: Dict[str, Any] = Depends(get_current_user_optional)):
    """Health check that works with or without authentication"""
    return {
        "status": "healthy",
        "authenticated": current_user is not None,
        "user_id": current_user["user_id"] if current_user else None
    }