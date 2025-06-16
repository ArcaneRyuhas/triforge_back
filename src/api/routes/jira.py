from fastapi import APIRouter, Depends, HTTPException
from src.models.requests import JiraUploadRequest, JiraValidateRequest
from src.models.responses import JiraUploadResponse, JiraValidationResponse
from src.services.jira_service import jira_service, JiraCredentials
from src.services.memory_service import memory_service
from src.utils.helpers import ContentFinder
from src.core.exceptions import AIServiceException, ValidationException
from src.utils.logger import logging
import secrets, base64, hashlib, httpx
import os
from urllib.parse import urlencode

router = APIRouter(prefix="/jira", tags=["jira"])
logger = logging.getLogger(__name__)
SESSION = {}

CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("JIRA_REDIRECT_URI", "http://localhost:3000/auth/jira/callback")

@router.post("/validate", response_model=JiraValidationResponse)
async def validate_jira_connection(request: JiraValidateRequest):
    """Validate Jira credentials and optionally project access"""
    try:
        credentials = JiraCredentials(
            email=request.email,
            api_token=request.api_token,
            domain=request.domain
        )
        
        creds_valid, creds_message = jira_service.validate_credentials(credentials)
        
        if not creds_valid:
            return JiraValidationResponse(
                user_id=request.user_id,
                is_valid=False,
                message=creds_message,
                project_validated=None
            )
        
        project_validated = None
        final_message = creds_message
        
        if request.project_key:
            project_valid, project_message = jira_service.validate_project(credentials, request.project_key)
            project_validated = project_valid
            final_message = f"{creds_message}. {project_message}"
        
        return JiraValidationResponse(
            user_id=request.user_id,
            is_valid=creds_valid,
            message=final_message,
            project_validated=project_validated
        )
        
    except Exception as e:
        logger.error(f"Error validating Jira connection: {str(e)}")
        raise AIServiceException(f"Error validating Jira connection: {str(e)}")

@router.post("/upload", response_model=JiraUploadResponse)
async def upload_stories_to_jira(request: JiraUploadRequest):
    """Upload Jira stories to Atlassian Jira Cloud"""
    try:
        stories_markdown = request.stories_markdown
        
        if not stories_markdown:
            shared_memory = memory_service.get_or_create_memory(request.user_id)
            memory_messages = shared_memory.chat_memory.messages
            stories_markdown = ContentFinder.find_jira_stories_in_memory(memory_messages)
            
            if not stories_markdown:
                raise ValidationException(
                    "No Jira stories provided in request or found in conversation history. "
                    "Please generate stories first or provide them in the request."
                )
        
        credentials = JiraCredentials(
            email=request.email,
            api_token=request.api_token,
            domain=request.domain
        )
        
        logger.info(f"Validating Jira connection for user {request.user_id}")
        creds_valid, creds_message = jira_service.validate_credentials(credentials)
        if not creds_valid:
            raise ValidationException(f"Jira credentials invalid: {creds_message}")
        
        project_valid, project_message = jira_service.validate_project(credentials, request.project_key)
        if not project_valid:
            raise ValidationException(f"Jira project invalid: {project_message}")
        
        logger.info(f"Parsing Jira stories from markdown for user {request.user_id}")
        stories = jira_service.parse_markdown_stories(stories_markdown)
        
        if not stories:
            raise ValidationException(
                "No valid stories found in the provided markdown. "
                "Please ensure stories are properly formatted with ## headers."
            )
        
        logger.info(f"Found {len(stories)} stories to upload for user {request.user_id}")
        
        upload_result = jira_service.upload_stories(credentials, request.project_key, stories)
        
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        shared_memory.save_context(
            {"input": f"Upload {len(stories)} stories to Jira project {request.project_key}"},
            {"output": upload_result.message}
        )
        
        if upload_result.success:
            logger.info(f"Successfully uploaded stories for user {request.user_id}: {upload_result.message}")
        else:
            logger.warning(f"Upload completed with issues for user {request.user_id}: {upload_result.message}")
        
        return JiraUploadResponse(
            user_id=request.user_id,
            success=upload_result.success,
            message=upload_result.message,
            created_issues=upload_result.created_issues,
            failed_issues=upload_result.failed_issues,
            total_stories=len(stories),
            successful_uploads=len(upload_result.created_issues)
        )
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error uploading stories to Jira: {str(e)}")
        raise AIServiceException(f"Error uploading stories to Jira: {str(e)}")

@router.get("/stories/{user_id}")
async def get_stories_from_memory(user_id: str):
    """Get the latest Jira stories from user's conversation memory"""
    try:
        shared_memory = memory_service.get_or_create_memory(user_id)
        memory_messages = shared_memory.chat_memory.messages
        stories_markdown = ContentFinder.find_jira_stories_in_memory(memory_messages)
        
        if not stories_markdown:
            raise ValidationException(
                f"No Jira stories found in conversation history for user {user_id}. "
                "Please generate stories first."
            )
        
        stories = jira_service.parse_markdown_stories(stories_markdown)
        
        return {
            "user_id": user_id,
            "stories_found": True,
            "stories_markdown": stories_markdown,
            "story_count": len(stories),
            "message": f"Found {len(stories)} stories in conversation history"
        }
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stories from memory: {str(e)}")
        raise AIServiceException(f"Error retrieving stories from memory: {str(e)}")
    
@router.get("/oauth2/start")
async def oauth_start():
    """Iniciar el flujo OAuth de Jira"""
    try:
        if not CLIENT_ID:
            logger.error("JIRA_CLIENT_ID not configured")
            raise HTTPException(status_code=500, detail="Jira OAuth not configured")
        
        state = secrets.token_urlsafe(16)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode()
        
        SESSION[state] = {"code_verifier": code_verifier}
        
        params = {
            "audience": "api.atlassian.com",
            "client_id": CLIENT_ID,
            "scope": "read:jira-work write:jira-work offline_access",
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        url = f"https://auth.atlassian.com/authorize?{urlencode(params)}"
        logger.info(f"Generated OAuth URL for state {state}")
        
        return {"authUrl": url}
        
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting OAuth flow: {str(e)}")

@router.get("/oauth2/callback")
async def oauth_callback(code: str, state: str):
    """Manejar el callback de OAuth"""
    try:
        if state not in SESSION:
            logger.error(f"Invalid state received: {state}")
            raise HTTPException(status_code=400, detail="Invalid state")
        
        code_verifier = SESSION.pop(state)["code_verifier"]
        
        if not CLIENT_ID or not CLIENT_SECRET:
            logger.error("OAuth credentials not configured")
            raise HTTPException(status_code=500, detail="OAuth credentials not configured")
        
        async with httpx.AsyncClient() as client:
            token_resp = await client.post("https://auth.atlassian.com/oauth/token", json={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": code_verifier
            })
            
            if not token_resp.is_success:
                logger.error(f"Token exchange failed: {token_resp.status_code} - {token_resp.text}")
                raise HTTPException(status_code=400, detail="Token exchange failed")
            
            tokens = token_resp.json()
            
            accessible_resources_resp = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            
            if accessible_resources_resp.is_success:
                resources = accessible_resources_resp.json()
                if resources:
                    tokens["cloud_id"] = resources[0]["id"]
                    tokens["site_url"] = resources[0]["url"]
            
            logger.info(f"OAuth flow completed successfully for state {state}")
            
            # Aquí se deberían guardar los tokens en una base de datos
            # vinculados al usuario actual
            
            return {"success": True, "tokens": tokens}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth callback error: {str(e)}")

@router.get("/debug/oauth-config")
async def debug_oauth_config():
    """Debug endpoint to check OAuth configuration"""
    return {
        "client_id_exists": bool(CLIENT_ID),
        "client_id_length": len(CLIENT_ID) if CLIENT_ID else 0,
        "client_secret_exists": bool(CLIENT_SECRET),
        "client_secret_length": len(CLIENT_SECRET) if CLIENT_SECRET else 0,
        "redirect_uri": REDIRECT_URI,
        "client_id_prefix": CLIENT_ID[:10] + "..." if CLIENT_ID and len(CLIENT_ID) > 10 else CLIENT_ID
    }

@router.post("/oauth2/refresh")
async def refresh_token(refresh_data: dict):
    """Refrescar el token de acceso"""
    try:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token required")
        
        if not CLIENT_ID or not CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="OAuth credentials not configured")
        
        async with httpx.AsyncClient() as client:
            token_resp = await client.post("https://auth.atlassian.com/oauth/token", json={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token
            })
            
            if not token_resp.is_success:
                logger.error(f"Token refresh failed: {token_resp.status_code} - {token_resp.text}")
                raise HTTPException(status_code=400, detail="Token refresh failed")
            
            tokens = token_resp.json()
            logger.info("Token refreshed successfully")
            
            return tokens
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")
    