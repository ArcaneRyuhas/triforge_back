import requests
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from src.core.exceptions import ValidationException, AIServiceException

logger = logging.getLogger(__name__)

@dataclass
class JiraCredentials:
    """Jira authentication credentials"""
    email: str
    api_token: str
    domain: str  

@dataclass
class JiraStory:
    """Parsed Jira story data"""
    title: str
    description: str
    acceptance_criteria: List[str]
    story_points: Optional[int] = None
    priority: Optional[str] = None

@dataclass
class JiraUploadResult:
    """Result of uploading stories to Jira"""
    success: bool
    created_issues: List[Dict[str, str]]  
    failed_issues: List[Dict[str, str]]   
    message: str

class JiraService:
    """Service for integrating with Atlassian Jira Cloud"""
    
    def __init__(self):
        self.base_url_template = "https://{domain}/rest/api/3"
        
    def validate_credentials(self, credentials: JiraCredentials) -> Tuple[bool, str]:
        """Validate Jira credentials and domain"""
        try:
            base_url = self.base_url_template.format(domain=credentials.domain)
            response = requests.get(
                f"{base_url}/myself",
                auth=(credentials.email, credentials.api_token),
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                return True, f"Connected as {user_info.get('displayName', credentials.email)}"
            elif response.status_code == 401:
                return False, "Invalid credentials - check email and API token"
            elif response.status_code == 404:
                return False, "Invalid domain - check your Atlassian domain"
            else:
                return False, f"Connection failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def validate_project(self, credentials: JiraCredentials, project_key: str) -> Tuple[bool, str]:
        """Validate that project exists and user has access"""
        try:
            base_url = self.base_url_template.format(domain=credentials.domain)
            response = requests.get(
                f"{base_url}/project/{project_key}",
                auth=(credentials.email, credentials.api_token),
                timeout=10
            )
            
            if response.status_code == 200:
                project_info = response.json()
                return True, f"Project found: {project_info.get('name', project_key)}"
            elif response.status_code == 404:
                return False, f"Project '{project_key}' not found or no access"
            elif response.status_code == 403:
                return False, f"No permission to access project '{project_key}'"
            else:
                return False, f"Project validation failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Project validation error: {str(e)}"
    
    def parse_markdown_stories(self, markdown_content: str) -> List[JiraStory]:
        """Parse Markdown content into JiraStory objects"""
        stories = []
        
        story_sections = re.split(r'\n##\s+', markdown_content)
        
        for section in story_sections:
            if not section.strip():
                continue
                
            try:
                story = self._parse_single_story(section)
                if story:
                    stories.append(story)
            except Exception as e:
                logger.warning(f"Failed to parse story section: {str(e)}")
                continue
        
        return stories
    
    def _parse_single_story(self, section: str) -> Optional[JiraStory]:
        """Parse a single story section"""
        lines = section.strip().split('\n')
        if not lines:
            return None
            
        title = lines[0].strip()
        if title.startswith('##'):
            title = title[2:].strip()
        
        description_lines = []
        acceptance_criteria = []
        story_points = None
        priority = None
        
        current_section = "description"
        
        for line in lines[1:]:
            line = line.strip()
            
            if not line:
                continue
                
            if "acceptance criteria" in line.lower():
                current_section = "acceptance"
                continue
            elif "story points" in line.lower():
                points_match = re.search(r'(\d+)', line)
                if points_match:
                    story_points = int(points_match.group(1))
                continue
            elif "priority" in line.lower():
                priority_match = re.search(r'(highest|high|medium|low|lowest)', line.lower())
                if priority_match:
                    priority = priority_match.group(1).title()
                continue
            
            if current_section == "description":
                description_lines.append(line)
            elif current_section == "acceptance":
                if line.startswith(('-', '*', '•')) or re.match(r'^\d+\.', line):
                    clean_line = re.sub(r'^[-*•]\s*', '', line)
                    clean_line = re.sub(r'^\d+\.\s*', '', clean_line)
                    acceptance_criteria.append(clean_line)
        
        description = '\n'.join(description_lines).strip()
        
        if not title:
            return None
            
        return JiraStory(
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            story_points=story_points,
            priority=priority
        )
    
    def upload_stories(
        self, 
        credentials: JiraCredentials, 
        project_key: str, 
        stories: List[JiraStory]
    ) -> JiraUploadResult:
        """Upload stories to Jira Cloud"""
        
        if not stories:
            return JiraUploadResult(
                success=False,
                created_issues=[],
                failed_issues=[],
                message="No stories to upload"
            )
        
        base_url = self.base_url_template.format(domain=credentials.domain)
        created_issues = []
        failed_issues = []
        
        for story in stories:
            try:
                issue_data = self._prepare_issue_data(project_key, story)
                
                response = requests.post(
                    f"{base_url}/issue",
                    json=issue_data,
                    auth=(credentials.email, credentials.api_token),
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 201:
                    created_issue = response.json()
                    created_issues.append({
                        "key": created_issue["key"],
                        "title": story.title,
                        "url": f"https://{credentials.domain}/browse/{created_issue['key']}"
                    })
                    logger.info(f"Created Jira issue: {created_issue['key']}")
                else:
                    error_detail = self._extract_error_message(response)
                    failed_issues.append({
                        "title": story.title,
                        "error": error_detail
                    })
                    logger.error(f"Failed to create issue '{story.title}': {error_detail}")
                    
            except Exception as e:
                failed_issues.append({
                    "title": story.title,
                    "error": str(e)
                })
                logger.error(f"Exception creating issue '{story.title}': {str(e)}")
        
        success = len(created_issues) > 0
        total_stories = len(stories)
        success_count = len(created_issues)
        
        if success_count == total_stories:
            message = f"Successfully uploaded all {total_stories} stories to Jira"
        elif success_count > 0:
            message = f"Uploaded {success_count}/{total_stories} stories to Jira"
        else:
            message = f"Failed to upload any stories to Jira"
        
        return JiraUploadResult(
            success=success,
            created_issues=created_issues,
            failed_issues=failed_issues,
            message=message
        )
    
    def _prepare_issue_data(self, project_key: str, story: JiraStory) -> Dict:
        """Prepare issue data for Jira API"""
        
        description_parts = []
        
        if story.description:
            description_parts.append(story.description)
        
        if story.acceptance_criteria:
            description_parts.append("\n*Acceptance Criteria:*")
            for i, criteria in enumerate(story.acceptance_criteria, 1):
                description_parts.append(f"{i}. {criteria}")
        
        if story.story_points:
            description_parts.append(f"\n*Story Points:* {story.story_points}")
        
        if story.priority:
            description_parts.append(f"\n*Priority:* {story.priority}")
        
        description = "\n".join(description_parts)
        
        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": story.title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": "Story"}
            }
        }
        
        
        return issue_data
    
    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract meaningful error message from Jira API response"""
        try:
            error_data = response.json()
            if "errors" in error_data:
                errors = []
                for field, message in error_data["errors"].items():
                    errors.append(f"{field}: {message}")
                return "; ".join(errors)
            elif "errorMessages" in error_data:
                return "; ".join(error_data["errorMessages"])
            else:
                return f"HTTP {response.status_code}: {response.text[:200]}"
        except:
            return f"HTTP {response.status_code}: {response.text[:200]}"

jira_service = JiraService()