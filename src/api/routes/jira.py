from fastapi import APIRouter, HTTPException
from src.models.requests import JiraUploadRequest, JiraValidateRequest
from src.models.responses import JiraUploadResponse, JiraValidationResponse
from src.services.jira_service import jira_service, JiraCredentials
from src.services.memory_service import memory_service
from src.utils.helpers import ContentFinder
from src.core.exceptions import AIServiceException, ValidationException
from src.utils.logger import logging

router = APIRouter(prefix="/jira", tags=["jira"])
logger = logging.getLogger(__name__)

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