from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.services.cognito_auth_service import cognito_auth_service
from src.utils.logger import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: The HTTP Bearer credentials containing the JWT token
        
    Returns:
        Dict containing user information extracted from the token
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = credentials.credentials
    
    # Verify the token and get claims
    claims = cognito_auth_service.verify_token(token)
    
    # Extract user information
    user_info = cognito_auth_service.extract_user_info(claims)
    
    return user_info

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns user info if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        claims = cognito_auth_service.verify_token(token)
        return cognito_auth_service.extract_user_info(claims)
    except HTTPException:
        return None

def require_groups(required_groups: list):
    """
    Dependency factory to require specific Cognito groups
    
    Args:
        required_groups: List of group names that are allowed access
        
    Returns:
        Dependency function that checks group membership
    """
    async def check_groups(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_groups = current_user.get("groups", [])
        
        if not any(group in user_groups for group in required_groups):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required groups: {', '.join(required_groups)}"
            )
        
        return current_user
    
    return check_groups

# Commonly used group dependencies
require_admin = require_groups(["admin"])
require_developer = require_groups(["developer", "admin"])
require_user = require_groups(["user", "developer", "admin"])