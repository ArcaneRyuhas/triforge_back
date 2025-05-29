import logging
import os
from pathlib import Path
from enum import StrEnum

LOG_FORMAT_DEBUG = "%(asctime)s - %(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"
LOG_FORMAT_STANDARD = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

class LogLevels(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

def configure_logging(log_level: str = LogLevels.ERROR, log_to_file: bool = True):
    log_level = str(log_level).upper()

    if log_level not in LogLevels.values():
        raise ValueError(f"Invalid log level: {log_level}. Must be one of {list(LogLevels)}")
    
    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "app.log"
    
    if log_level == LogLevels.DEBUG:
        format_str = LOG_FORMAT_DEBUG
    else:
        format_str = LOG_FORMAT_STANDARD
    
    if log_to_file:
        logging.basicConfig(
            level=log_level,
            format=format_str,
            handlers=[
                logging.FileHandler(log_file),  
                logging.StreamHandler()        
            ]
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=format_str
        )