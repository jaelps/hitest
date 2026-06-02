import logging
import os
from pathlib import Path
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Format logs as [YYYY-MM-DD HH:MM:SS] Message"""
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        return f"[{timestamp}] {record.getMessage()}"

def setup_logger() -> logging.Logger:
    """Configures and returns the application logger."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "hitest.log"

    logger = logging.getLogger("Hitest")
    logger.setLevel(logging.INFO)

    # Prevent adding duplicate handlers if logger is configured multiple times
    if not logger.handlers:
        # File Handler
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setFormatter(CustomFormatter())
        logger.addHandler(file_handler)

        # Stream Handler (console output)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)

    return logger

# Global logger instance
logger = setup_logger()
