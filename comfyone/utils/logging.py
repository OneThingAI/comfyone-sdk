import logging
import sys
from typing import Optional
from pathlib import Path

def setup_logger(
    name: str = "comfyone",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
) -> logging.Logger:
    """Configure logging for the ComfyOne SDK"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger 