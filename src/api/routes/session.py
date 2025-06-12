# Create new file: src/api/routes/session.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from src.models.requests import BaseModel
from src.models.responses import BaseModel as ResponseModel
from src.api.auth_dependencies import get_current_user
from src.services.memory_service import memory_service
from src.core.config import settings
from src.utils.logger import logging
import hmac
import hashlib
import base64

router = APIRouter(prefix="/session", tags=["session"])
logger = logging.getLogger(__name__)

# Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginResponse(ResponseModel):
    access_token: str
    id_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    user_info: Dict[str, Any]

class SessionResponse(ResponseModel):
    session_id: str
    user_id: str
    email: str
    username: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True

class RefreshResponse(ResponseModel):
    access_token: str
    id_token: str
    expires_in: int
    token_type: str = "Bearer"

# Initialize Cognito client
cognito_client = boto3.client(
    'cognito-idp',
    region_name=settings.cognito_region
)

def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calculate SECRET_HASH for Cognito if using app client with secret"""
    message = username + client_id
    dig = hmac.new(
        str(client_secret).encode('UTF-8'),
        msg=str(message).encode('UTF-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with Cognito and start a session.
    Returns JWT tokens that can be used for subsequent API calls.
    """
    try:
        # Prepare authentication parameters
        auth_params = {
            'USERNAME': request.username,
            'PASSWORD': request.password
        }
        
        # If your app client has a secret, uncomment and set COGNITO_CLIENT_SECRET in .env
        # if hasattr(settings, 'cognito_client_secret') and settings.cognito_client_secret:
        #     auth_params['SECRET_HASH'] = calculate_secret_hash(
        #         request.username,
        #         settings.cognito_app_client_id,
        #         settings.cognito_client_secret
        #     )
        
        # Authenticate with Cognito
        response = cognito_client.initiate_auth(
            ClientId=settings.cognito_app_client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters=auth_params
        )
        
        # Extract tokens
        auth_result = response['AuthenticationResult']
        
        # Get user info from the ID token
        user_response = cognito_client.get_user(
            AccessToken=auth_result['AccessToken']
        )
        
        # Extract user attributes
        user_attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
        
        # Create user info
        user_info = {
            'user_id': user_attributes.get('sub'),
            'email': user_attributes.get('email'),
            'username': user_response['Username'],
            'email_verified': user_attributes.get('email_verified', 'false') == 'true',
            'groups': user_response.get('UserGroups', [])
        }
        
        # Initialize memory for the user
        memory_service.get_or_create_memory(user_info['user_id'])
        
        logger.info(f"User {user_info['username']} logged in successfully")
        
        return LoginResponse(
            access_token=auth_result['AccessToken'],
            id_token=auth_result['IdToken'],
            refresh_token=auth_result['RefreshToken'],
            expires_in=auth_result['ExpiresIn'],
            user_info=user_info
        )
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'NotAuthorizedException':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        elif error_code == 'UserNotConfirmedException':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User email not confirmed"
            )
        elif error_code == 'UserNotFoundException':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        else:
            logger.error(f"Cognito error: {error_code} - {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication failed: {error_message}"
            )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    Use this when the access token expires (typically after 1 hour).
    """
    try:
        response = cognito_client.initiate_auth(
            ClientId=settings.cognito_app_client_id,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': request.refresh_token
            }
        )
        
        auth_result = response['AuthenticationResult']
        
        return RefreshResponse(
            access_token=auth_result['AccessToken'],
            id_token=auth_result['IdToken'],
            expires_in=auth_result['ExpiresIn']
        )
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NotAuthorizedException':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout user and clear their session.
    Note: This doesn't invalidate the JWT token (which will remain valid until expiry),
    but it clears server-side session data.
    """
    try:
        user_id = current_user['user_id']
        
        # Clear user's memory/conversation history
        memory_service.clear_memory(user_id)
        
        # In production, you might want to:
        # 1. Add the token to a blacklist (Redis)
        # 2. Call Cognito's global sign out endpoint
        # 3. Clear any server-side session data
        
        logger.info(f"User {current_user['username']} logged out")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )

@router.get("/current", response_model=SessionResponse)
async def get_current_session(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current session information for authenticated user.
    """
    try:
        # Calculate session expiry from token exp claim
        exp_timestamp = current_user.get('exp', 0)
        expires_at = datetime.fromtimestamp(exp_timestamp)
        
        # Calculate created_at (iat - issued at time)
        iat_timestamp = current_user.get('iat', 0)
        created_at = datetime.fromtimestamp(iat_timestamp)
        
        return SessionResponse(
            session_id=f"session_{current_user['user_id']}_{iat_timestamp}",
            user_id=current_user['user_id'],
            email=current_user.get('email', ''),
            username=current_user.get('username', ''),
            created_at=created_at,
            expires_at=expires_at,
            is_active=True
        )
        
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )

@router.post("/validate")
async def validate_session(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Validate current session/token.
    Returns user info if token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user['user_id'],
        "username": current_user.get('username'),
        "email": current_user.get('email'),
        "groups": current_user.get('groups', []),
        "expires_at": datetime.fromtimestamp(current_user.get('exp', 0)).isoformat()
    }