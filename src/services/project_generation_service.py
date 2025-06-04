# Create new file: src/services/project_generation_service.py

import json
import zipfile
import tempfile
import os
from uuid import uuid4
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
from src.models.responses import ProjectFile
from src.core.exceptions import AIServiceException, ValidationException

logger = logging.getLogger(__name__)

@dataclass
class Technology:
    """Represents a detected technology"""
    name: str
    category: str  # frontend, backend, database, etc.
    version: Optional[str] = None

@dataclass
class ProjectStructure:
    """Represents the structure of a generated project"""
    project_id: str
    technologies: List[Technology]
    files: List[ProjectFile]
    root_structure: Dict[str, Any]

class ProjectGenerationService:
    """Service for generating complete project structures with multiple technologies"""
    
    def __init__(self):
        self.generated_projects: Dict[str, ProjectStructure] = {}
        self.temp_files: Dict[str, str] = {}
    
    def parse_technologies(self, llm_response: str) -> List[Technology]:
        """Parse technologies from LLM response"""
        try:
            # Import the cleaner here to avoid circular imports
            from src.utils.helpers import JSONResponseCleaner
            
            # Clean and parse the response
            clean_response = JSONResponseCleaner.clean_json_response(llm_response)
            logger.info(f"Cleaned technology response: {clean_response[:200]}...")
            
            # Parse JSON
            data = json.loads(clean_response)
            technologies = []
            
            for tech_data in data.get("technologies", []):
                tech = Technology(
                    name=tech_data.get("name", ""),
                    category=tech_data.get("category", "unknown"),
                    version=tech_data.get("version")
                )
                technologies.append(tech)
            
            logger.info(f"Parsed {len(technologies)} technologies")
            return technologies
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse technologies JSON: {str(e)}")
            logger.error(f"Raw response: {llm_response}")
            raise ValidationException(f"Invalid technology detection response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing technologies: {str(e)}")
            raise AIServiceException(f"Error parsing technologies: {str(e)}")
    
    def parse_project_files(self, llm_response: str) -> List[ProjectFile]:
        """Parse project files from LLM response"""
        try:
            # Import the cleaner here to avoid circular imports
            from src.utils.helpers import JSONResponseCleaner
            
            # Clean and parse the response
            clean_response = JSONResponseCleaner.clean_json_response(llm_response)
            logger.info(f"Cleaned project files response length: {len(clean_response)}")
            
            # Parse JSON
            data = json.loads(clean_response)
            files = []
            
            for file_data in data.get("files", []):
                file_obj = ProjectFile(
                    path=file_data.get("path", ""),
                    content=file_data.get("content", ""),
                    language=file_data.get("language", "text")
                )
                files.append(file_obj)
            
            logger.info(f"Parsed {len(files)} project files")
            return files
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse project files JSON: {str(e)}")
            logger.error(f"Raw response length: {len(llm_response)}, first 500 chars: {llm_response[:500]}")
            raise ValidationException(f"Invalid project files response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing project files: {str(e)}")
            raise AIServiceException(f"Error parsing project files: {str(e)}")
    
    def create_project_structure(self, files: List[ProjectFile]) -> Dict[str, Any]:
        """Create a hierarchical structure representation of the project"""
        structure = {}
        
        for file in files:
            parts = file.path.split('/')
            current = structure
            
            # Navigate/create the directory structure
            for part in parts[:-1]:  # All except the last part (filename)
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Add the file
            filename = parts[-1]
            current[filename] = {
                "type": "file",
                "language": file.language,
                "size": len(file.content)
            }
        
        return structure
    
    def store_project(self, project_id: str, technologies: List[Technology], 
                     files: List[ProjectFile]) -> ProjectStructure:
        """Store generated project in memory"""
        try:
            root_structure = self.create_project_structure(files)
            
            project = ProjectStructure(
                project_id=project_id,
                technologies=technologies,
                files=files,
                root_structure=root_structure
            )
            
            self.generated_projects[project_id] = project
            logger.info(f"Stored project {project_id} with {len(files)} files")
            
            return project
            
        except Exception as e:
            logger.error(f"Error storing project {project_id}: {str(e)}")
            raise AIServiceException(f"Error storing project: {str(e)}")
    
    def get_project(self, project_id: str) -> Optional[ProjectStructure]:
        """Retrieve a stored project"""
        return self.generated_projects.get(project_id)
    
    def create_zip_file(self, project_id: str) -> str:
        """Create a ZIP file for the project and return the file path"""
        try:
            project = self.get_project(project_id)
            if not project:
                raise ValidationException(f"Project {project_id} not found")
            
            # Create temporary directory and ZIP file
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, f"project_{project_id}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all project files
                for file in project.files:
                    zipf.writestr(file.path, file.content)
                
                # Add README if not already present
                readme_exists = any(file.path.lower().startswith('readme') for file in project.files)
                if not readme_exists:
                    readme_content = self._generate_readme(project)
                    zipf.writestr("README.md", readme_content)
            
            # Store the temp file path for cleanup later
            self.temp_files[project_id] = zip_path
            
            logger.info(f"Created ZIP file for project {project_id}: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error creating ZIP file for project {project_id}: {str(e)}")
            raise AIServiceException(f"Error creating ZIP file: {str(e)}")
    
    def _generate_readme(self, project: ProjectStructure) -> str:
        """Generate a README.md file for the project"""
        tech_list = ", ".join([tech.name for tech in project.technologies])
        
        readme = f"""# Generated Project

## Technologies Used
{tech_list}

## Project Structure
This project was generated with the following technologies:

"""
        
        for tech in project.technologies:
            readme += f"- **{tech.name}** ({tech.category})"
            if tech.version:
                readme += f" - Version: {tech.version}"
            readme += "\n"
        
        readme += f"""
## Installation & Deployment

### Prerequisites
Make sure you have the following installed:
"""
        
        # Add specific prerequisites based on technologies
        for tech in project.technologies:
            if tech.name.lower() in ["next.js", "nextjs", "react"]:
                readme += "- Node.js (v18 or higher)\n- npm or yarn\n"
            elif tech.name.lower() in ["nest.js", "nestjs"]:
                readme += "- Node.js (v18 or higher)\n- npm or yarn\n"
            elif tech.name.lower() in ["mongodb", "mongo"]:
                readme += "- MongoDB (local or cloud instance)\n"
            elif tech.name.lower() == "python":
                readme += "- Python (v3.8 or higher)\n- pip\n"
        
        readme += """
### Setup Instructions

1. **Install Dependencies**
   ```bash
   # For Node.js projects
   npm install
   # or
   yarn install
   ```

2. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Configure your database connection strings
   - Set up any required API keys

3. **Database Setup**
   - Ensure your database is running
   - Run migrations if applicable

4. **Start the Application**
   ```bash
   # Development mode
   npm run dev
   # or
   yarn dev
   ```

## File Structure
"""
        
        # Add file structure
        def add_structure(structure, indent=0):
            result = ""
            for key, value in structure.items():
                result += "  " * indent + f"- {key}\n"
                if isinstance(value, dict) and "type" not in value:
                    result += add_structure(value, indent + 1)
            return result
        
        readme += add_structure(project.root_structure)
        
        readme += """
## Generated by TriForge AI Documentation System

This project structure was automatically generated based on your requirements.
Please review and modify the code as needed for your specific use case.
"""
        
        return readme
    
    def cleanup_temp_file(self, project_id: str):
        """Clean up temporary ZIP file"""
        if project_id in self.temp_files:
            temp_path = self.temp_files[project_id]
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    # Also try to remove the temp directory if empty
                    temp_dir = os.path.dirname(temp_path)
                    try:
                        os.rmdir(temp_dir)
                    except OSError:
                        pass  # Directory not empty, ignore
                del self.temp_files[project_id]
                logger.info(f"Cleaned up temp file for project {project_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file for project {project_id}: {str(e)}")

# Global instance
project_generation_service = ProjectGenerationService()