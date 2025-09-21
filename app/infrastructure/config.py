"""
Configuration management for the notification service.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from structlog import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "notification_service"
    username: str = "postgres"
    password: str = "password"
    echo: bool = False
    
    @property
    def url(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    @property
    def url(self) -> str:
        """Get Redis URL."""
        auth_part = f":{self.password}@" if self.password else ""
        return f"redis://{auth_part}{self.host}:{self.port}/{self.db}"


@dataclass
class EmailConfig:
    """Email provider configuration."""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    from_address: str = "noreply@example.com"
    from_name: str = "Notification Service"


@dataclass
class SMSConfig:
    """SMS provider configuration."""
    provider: str = "twilio"
    account_sid: str = ""
    auth_token: str = ""
    from_number: str = ""


@dataclass
class TelegramConfig:
    """Telegram provider configuration."""
    bot_token: str = ""
    parse_mode: str = "HTML"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    enable_colors: bool = True


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list = field(default_factory=lambda: ["*"])
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass
class Config:
    """Main application configuration."""
    environment: str = "development"
    debug: bool = False
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    sms: SMSConfig = field(default_factory=SMSConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            
            database=DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "notification_service"),
                username=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "password"),
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            ),
            
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                password=os.getenv("REDIS_PASSWORD"),
            ),
            
            email=EmailConfig(
                smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                username=os.getenv("SMTP_USERNAME", ""),
                password=os.getenv("SMTP_PASSWORD", ""),
                use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
                from_address=os.getenv("SMTP_FROM_ADDRESS", "noreply@example.com"),
                from_name=os.getenv("SMTP_FROM_NAME", "Notification Service"),
            ),
            
            sms=SMSConfig(
                provider=os.getenv("SMS_PROVIDER", "twilio"),
                account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
                auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
                from_number=os.getenv("TWILIO_FROM_NUMBER", ""),
            ),
            
            telegram=TelegramConfig(
                bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
                parse_mode=os.getenv("TELEGRAM_PARSE_MODE", "HTML"),
            ),
            
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                format=os.getenv("LOG_FORMAT", "json"),
                enable_colors=os.getenv("LOG_COLORS", "true").lower() == "true",
            ),
            
            api=APIConfig(
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8000")),
                debug=os.getenv("API_DEBUG", "false").lower() == "true",
                cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
                docs_url=os.getenv("API_DOCS_URL", "/docs"),
                redoc_url=os.getenv("API_REDOC_URL", "/redoc"),
            ),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if self.environment not in ["development", "testing", "production"]:
            raise ValueError(f"Invalid environment: {self.environment}")
        
        if self.environment == "production":
            # Validate production-critical settings
            if not self.database.password:
                logger.warning("Database password not set in production")
            
            if not self.email.password and self.email.username:
                logger.warning("Email password not set but username provided")
            
            if not self.sms.auth_token and self.sms.account_sid:
                logger.warning("SMS auth token not set but account SID provided")
            
            if not self.telegram.bot_token:
                logger.warning("Telegram bot token not set")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.validate()
        logger.info("Configuration loaded", environment=_config.environment)
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
    logger.info("Configuration updated", environment=config.environment)