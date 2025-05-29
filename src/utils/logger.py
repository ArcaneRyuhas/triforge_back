import logging
import logging.handlers
from pathlib import Path
from enum import StrEnum

LOG_FORMAT_DEBUG = "%(asctime)s - %(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"
LOG_FORMAT_STANDARD = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

class LogLevels(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

def configure_logging(
    log_level: str = LogLevels.ERROR,
    log_to_file: bool = True,
    max_file_size_mb: int = 10,
    backup_count: int = 5
):
    """
    Configure logging with file rotation and console output.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to save logs to files
        max_file_size_mb: Maximum size of each log file in MB
        backup_count: Number of backup log files to keep
    """
    log_level = str(log_level).upper()

    # Fix: Use list(LogLevels) instead of LogLevels.values()
    if log_level not in [level.value for level in LogLevels]:
        raise ValueError(f"Invalid log level: {log_level}. Must be one of {[level.value for level in LogLevels]}")
    
    # Choose format based on log level
    if log_level == LogLevels.DEBUG:
        format_str = LOG_FORMAT_DEBUG
    else:
        format_str = LOG_FORMAT_STANDARD
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    handlers = []
    
    # File handler with rotation
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(format_str))
        handlers.append(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format_str))
    handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=handlers,
        force=True  # This overwrites any existing configuration
    )