import json
import traceback
import os
from fastapi import APIRouter, HTTPException
from src.models.requests import CodeGenerationRequest, ModifyCodeRequest
from src.models.responses import ConversationResponse
from src.services.chain_factory import chain_factory 
from src.services.memory_service import memory_service 
from src.utils.helpers import ResponseCleaner, ContentFinder
from src.core.exceptions import AIServiceException, ValidationException
from src.utils.logger import logging
from uuid import uuid4
from fastapi.responses import FileResponse
from src.models.requests import ProjectCodeGenerationRequest, ProjectStructureRequest, ProjectDownloadRequest
from src.models.responses import ProjectCodeResponse, ProjectStructureResponse, DownloadResponse
from src.services.project_generation_service import project_generation_service
from src.utils.helpers import ContentFinder, ContextGatherer

router = APIRouter(prefix="/code", tags=["code"])
logger = logging.getLogger(__name__)

@router.post("/generate-project", response_model=ProjectCodeResponse)
async def generate_project_code(request: ProjectCodeGenerationRequest):
    """Generate a complete project with multiple technologies based on user prompt."""
    try:
        project_id = str(uuid4())
        
        # Get context from memory (requirements, documentation, diagrams)
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        memory_messages = shared_memory.chat_memory.messages
        
        # Use ContextGatherer to collect and format context
        context_data = ContextGatherer.gather_project_context(memory_messages)
        context = ContextGatherer.format_context_for_llm(context_data)
        
        logger.info(f"Starting project generation for user {request.user_id} with prompt: {request.prompt[:100]}...")
        
        # Step 1: Detect technologies
        technology_chain = chain_factory.create_technology_detection_chain(request.user_id)
        
        tech_response = technology_chain.predict(
            prompt=request.prompt,
            context=context
        )
        
        logger.info(f"Technology detection response: {tech_response}")
        
        # Parse technologies
        technologies = project_generation_service.parse_technologies(tech_response)
        
        if not technologies:
            raise ValidationException("No technologies could be detected from your prompt. Please be more specific about the technologies you want to use.")
        
        logger.info(f"Detected {len(technologies)} technologies: {[tech.name for tech in technologies]}")
        
        # Step 2: Generate project code
        project_chain = chain_factory.create_project_code_generation_chain(request.user_id)
        
        technologies_str = json.dumps([
            {"name": tech.name, "category": tech.category, "version": tech.version}
            for tech in technologies
        ], indent=2)
        
        full_input = f"""
            Technologies to use:
            {technologies_str}

            User Requirements:
            {request.prompt}

            Context from Memory (requirements, documentation, diagrams):
            {context}
            """

        if shared_memory.chat_memory.messages:
            full_input += f"\n\nChat History:\n{str(shared_memory.chat_memory.messages)}"

        code_response = project_chain.invoke(full_input)
        
        logger.info(f"Project code generation completed, response length: {len(code_response)}")
        if isinstance(code_response, dict) and 'text' in code_response:
            actual_response = code_response['text']
        else:
            actual_response = str(code_response)
        # Parse project files
        project_files = project_generation_service.parse_project_files(actual_response)
        
        if not project_files:
            raise ValidationException("No project files could be generated. Please try again with a different prompt.")
        
        logger.info(f"Generated {len(project_files)} project files")
        
        # Store the project
        project_structure = project_generation_service.store_project(
            project_id, technologies, project_files
        )
        
        # Generate README content
        readme_content = project_generation_service._generate_readme(project_structure)
        
        # Save to memory
        shared_memory.save_context(
            {"input": f"Generate project with technologies: {', '.join([tech.name for tech in technologies])}"}, 
            {"output": f"Generated complete project with {len(project_files)} files using: {', '.join([tech.name for tech in technologies])}"}
        )
        
        logger.info(f"Successfully generated project {project_id} for user {request.user_id}")
        
        return ProjectCodeResponse(
            user_id=request.user_id,
            project_id=project_id,
            technologies=[tech.name for tech in technologies],
            files=project_files,
            project_structure=project_structure.root_structure,
            readme_content=readme_content,
            message=f"Successfully generated project with {len(project_files)} files using {', '.join([tech.name for tech in technologies])}"
        )
        
    except Exception as e:
        logger.error(f"Error generating project code: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise AIServiceException(f"Error generating project code: {str(e)}")

@router.post("/project-structure", response_model=ProjectStructureResponse)
async def get_project_structure(request: ProjectStructureRequest):
    """Get the structure of a previously generated project."""
    try:
        project = project_generation_service.get_project(request.project_id)
        
        if not project:
            raise ValidationException(f"Project {request.project_id} not found")
        
        logger.info(f"Retrieved structure for project {request.project_id}")
        
        return ProjectStructureResponse(
            user_id=request.user_id,
            project_id=request.project_id,
            structure=project.root_structure,
            total_files=len(project.files)
        )
        
    except Exception as e:
        logger.error(f"Error getting project structure: {str(e)}")
        raise AIServiceException(f"Error getting project structure: {str(e)}")

@router.post("/download-project", response_model=DownloadResponse)
async def prepare_project_download(request: ProjectDownloadRequest):
    """Prepare a project for download as ZIP file."""
    try:
        project = project_generation_service.get_project(request.project_id)
        
        if not project:
            raise ValidationException(f"Project {request.project_id} not found")
        
        # Create ZIP file
        zip_path = project_generation_service.create_zip_file(request.project_id)
        
        # Get file size
        file_size = os.path.getsize(zip_path)
        filename = f"project_{request.project_id}.zip"
        
        logger.info(f"Prepared download for project {request.project_id}, size: {file_size} bytes")
        
        return DownloadResponse(
            user_id=request.user_id,
            project_id=request.project_id,
            download_url=f"/code/download-zip/{request.project_id}",
            filename=filename,
            size_bytes=file_size
        )
        
    except Exception as e:
        logger.error(f"Error preparing project download: {str(e)}")
        raise AIServiceException(f"Error preparing project download: {str(e)}")

@router.get("/download-zip/{project_id}")
async def download_project_zip(project_id: str):
    """Download the ZIP file for a project."""
    try:
        project = project_generation_service.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        zip_path = project_generation_service.temp_files.get(project_id)
        
        if not zip_path or not os.path.exists(zip_path):
            # Recreate ZIP if it doesn't exist
            zip_path = project_generation_service.create_zip_file(project_id)
        
        filename = f"project_{project_id}.zip"
        
        logger.info(f"Serving download for project {project_id}")
        
        return FileResponse(
            path=zip_path,
            media_type='application/zip',
            filename=filename,
            background=lambda: project_generation_service.cleanup_temp_file(project_id)
        )
        
    except Exception as e:
        logger.error(f"Error downloading project ZIP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading project: {str(e)}")

@router.delete("/project/{project_id}")
async def delete_project(project_id: str, user_id: str):
    """Delete a generated project from memory."""
    try:
        project = project_generation_service.get_project(project_id)
        
        if not project:
            raise ValidationException(f"Project {project_id} not found")
        
        # Clean up temp files
        project_generation_service.cleanup_temp_file(project_id)
        
        # Remove from memory
        if project_id in project_generation_service.generated_projects:
            del project_generation_service.generated_projects[project_id]
        
        logger.info(f"Deleted project {project_id}")
        
        return {"message": f"Project {project_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise AIServiceException(f"Error deleting project: {str(e)}")