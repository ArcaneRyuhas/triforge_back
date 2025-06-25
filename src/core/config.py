from pydantic_settings import BaseSettings
from typing import List
from src.utils.logger import LogLevels


class Settings(BaseSettings):
    # API Settings
    app_name: str = "AI Documentation API"
    version: str = "1.0.0"
    debug: bool = False
    
    # AI Configuration
    genai_api_key: str
    default_model: str = "gemini-2.0-flash"
    
    # CORS Settings
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Chain Configuration
    memory_window_size: int = 4
    default_temperature: float = 0.2
    max_output_tokens: int = 400

    # Logging Configuration
    log_level: str = LogLevels.INFO
    log_to_file: bool = True
    max_log_file_size_mb: int = 10
    log_backup_count: int = 5
    
    # AWS Cognito Configuration
    cognito_region: str = "us-east-1"  # Change to your region
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_domain: str = ""  # Optional: for hosted UI
    cognito_jwks_url: str = ""  # Will be constructed from region and pool ID
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def model_post_init(self, __context) -> None:
        """Construct JWKS URL after initialization"""
        if self.cognito_user_pool_id and self.cognito_region:
            self.cognito_jwks_url = f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json"
            
        # Validate required fields
        if not self.genai_api_key:
            raise ValueError("GENAI_API_KEY environment variable is required")

settings = Settings()