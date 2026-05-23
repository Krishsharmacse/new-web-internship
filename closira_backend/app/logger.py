import logging
import sys
from pythonjsonlogger import jsonlogger

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        
        # Use python-json-logger for structured logging
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = get_logger("closira_backend")
