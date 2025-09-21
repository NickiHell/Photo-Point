"""
Logging configuration and setup.
"""
import logging
import sys

try:
    import structlog
    from structlog.stdlib import LoggerFactory

    def setup_logging(config) -> None:
        """Setup structured logging with structlog."""
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, config.level.upper(), logging.INFO)
        )

        # Configure structlog
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="ISO", utc=True),
        ]

        if config.format == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            if config.enable_colors:
                processors.append(structlog.dev.ConsoleRenderer(colors=True))
            else:
                processors.append(structlog.dev.ConsoleRenderer(colors=False))

        structlog.configure(
            processors=processors,
            logger_factory=LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def get_logger(name: str = None):
        """Get a structured logger instance."""
        return structlog.get_logger(name)

except ImportError:
    # Fallback to standard logging when structlog is not available
    def setup_logging(config) -> None:
        """Setup standard logging."""
        logging.basicConfig(
            level=getattr(logging, config.level.upper(), logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def get_logger(name: str = None):
        """Get a standard logger instance."""
        return logging.getLogger(name or __name__)
