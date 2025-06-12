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
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.genai_api_key:
            raise ValueError("GENAI_API_KEY environment variable is required")

settings = Settings()