"""
Logging utilities for ZeroToShip.
"""

import logging
import structlog
from typing import Optional


def setup_logging(level: str = "INFO", structured: bool = True) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Log level
        structured: Enable structured logging
    """
    if structured:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger
    """
    return structlog.get_logger(name) 