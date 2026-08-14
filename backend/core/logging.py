import sys
from loguru import logger

# Remove default logger handler
logger.remove()

# Add customized stdout logger
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

# Add file logger for persistent records
logger.add(
    "logs/migraq.log",
    rotation="10 MB",
    retention="14 days",
    level="DEBUG",
    encoding="utf-8",
)

export_logger = logger
