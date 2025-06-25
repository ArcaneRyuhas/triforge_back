import json
import time
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWKClient
import requests
from fastapi import HTTPException, status
from src.core.config import settings
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class CognitoAuthService:
    """Service for handling AWS Cognito authentication"""
    
    def __init__(self):
        self.region = settings.cognito_region
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_app_client_id
        self.jwks_url = settings.cognito_jwks_url
        self.jwk_client = None
        
        if self.jwks_url:
            try:
                self.jwk_client = PyJWKClient(self.jwks_url)
                logger.info(f"Initialized Cognito JWT client with JWKS URL: {self.jwks_url}")
            except Exception as e:
                logger.error(f"Failed to initialize JWK client: {str(e)}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a Cognito JWT token
        
        Args:
            token: The JWT token string
            
        Returns:
            Dict containing the decoded token claims
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            if not self.jwk_client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cognito authentication not properly configured"
                )
            
            signing_key = self.jwk_client.get_signing_key_from_jwt(token)
            
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}",
                options={
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            
            if claims.get("token_use") not in ["id", "access"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            logger.info(f"Successfully verified token for user: {claims.get('sub')}")
            return claims
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def extract_user_info(self, claims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from token claims
        
        Args:
            claims: The decoded JWT claims
            
        Returns:
            Dict containing user information
        """
        return {
            "user_id": claims.get("sub"),  
            "email": claims.get("email"),
            "username": claims.get("cognito:username", claims.get("preferred_username")),
            "groups": claims.get("cognito:groups", []),
            "token_use": claims.get("token_use"),
            "exp": claims.get("exp"),
            "iat": claims.get("iat")
        }
    
    def is_token_expired(self, claims: Dict[str, Any]) -> bool:
        """Check if token is expired based on claims"""
        exp = claims.get("exp", 0)
        return exp < time.time()
    
    def get_user_groups(self, claims: Dict[str, Any]) -> list:
        """Extract user groups from token claims"""
        return claims.get("cognito:groups", [])
    
    def has_required_group(self, claims: Dict[str, Any], required_groups: list) -> bool:
        """Check if user has any of the required groups"""
        user_groups = self.get_user_groups(claims)
        return any(group in user_groups for group in required_groups)

cognito_auth_service = CognitoAuthService()