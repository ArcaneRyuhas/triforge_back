import logging
from enum import StrEnum

LOG_FORMAT_DEBUG = "%(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"

class LogLevels(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

def configure_logging(log_level: str = LogLevels.ERROR):
    log_level = str(log_level).upper()

    if log_level not in LogLevels.values():
        raise ValueError(f"Invalid log level: {log_level}. Must be one of {list(LogLevels)}")
    
    elif log_level == LogLevels.DEBUG:
        logging.basicConfig(
            level=log_level,
            format=LOG_FORMAT_DEBUG,
        )
    
    else:
        logging.basicConfig(level=log_level)