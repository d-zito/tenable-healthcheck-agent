import logging
import sys
from pathlib import Path


def setup_logger(name='tenable-healthcheck', log_level=logging.INFO):
    """
    Set up a logger with both file and console handlers.

    Args:
        name: Logger name
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # File handler - detailed logs
    file_handler = logging.FileHandler(log_dir / 'healthcheck.log')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    # Console handler - user-friendly output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
