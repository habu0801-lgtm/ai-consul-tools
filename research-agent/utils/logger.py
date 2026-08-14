import logging
import json
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """Setup logger with JSON formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_json(data: dict, log_file: str = None) -> None:
    """Log data as JSON format."""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json_str + "\n")
    else:
        print(json_str)
