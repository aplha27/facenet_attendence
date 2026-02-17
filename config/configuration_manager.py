"""
Configuration Manager for the Attendance System

Handles loading configuration from environment variables, configuration files,
and provides default values with proper validation.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import configparser

logger = logging.getLogger(__name__)


@dataclass
class SystemConfig:
    """System configuration data class"""
    database_url: str
    upload_directory: Path
    model_directory: Path
    reports_directory: Path
    allowed_file_types: List[str]
    max_file_size: int
    face_detection_threshold: float
    recognition_threshold: float
    secret_key: str
    debug: bool


class ConfigurationManager:
    """Manages system configuration from multiple sources"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Optional path to configuration file
        """
        self._config = None
        self._config_file = config_file or "config.ini"
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from environment variables and config files"""
        # Load environment variables from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment variables from .env file")
        
        # Load from config file if it exists
        config_parser = configparser.ConfigParser()
        config_file_path = Path(self._config_file)
        
        if config_file_path.exists():
            config_parser.read(config_file_path)
            logger.info(f"Loaded configuration from {config_file_path}")
        else:
            logger.warning(f"Configuration file {config_file_path} not found, using defaults")
        
        # Build configuration with precedence: env vars > config file > defaults
        self._config = SystemConfig(
            database_url=self._get_config_value(
                "DATABASE_URL", 
                config_parser, 
                "database", 
                "url", 
                "sqlite:///attendance.db"
            ),
            upload_directory=Path(self._get_config_value(
                "UPLOAD_DIRECTORY",
                config_parser,
                "paths",
                "upload_directory",
                "uploads"
            )),
            model_directory=Path(self._get_config_value(
                "MODEL_DIRECTORY",
                config_parser,
                "paths",
                "model_directory",
                "attendance/facenet/src/20180402-114759"
            )),
            reports_directory=Path(self._get_config_value(
                "REPORTS_DIRECTORY",
                config_parser,
                "paths",
                "reports_directory",
                "reports"
            )),
            allowed_file_types=self._get_list_config_value(
                "ALLOWED_FILE_TYPES",
                config_parser,
                "security",
                "allowed_file_types",
                ["jpg", "jpeg", "png", "bmp"]
            ),
            max_file_size=int(self._get_config_value(
                "MAX_FILE_SIZE",
                config_parser,
                "security",
                "max_file_size",
                "10485760"  # 10MB
            )),
            face_detection_threshold=float(self._get_config_value(
                "FACE_DETECTION_THRESHOLD",
                config_parser,
                "face_recognition",
                "detection_threshold",
                "0.6"
            )),
            recognition_threshold=float(self._get_config_value(
                "RECOGNITION_THRESHOLD",
                config_parser,
                "face_recognition",
                "recognition_threshold",
                "0.43"
            )),
            secret_key=self._get_config_value(
                "SECRET_KEY",
                config_parser,
                "security",
                "secret_key",
                "dev-secret-key-change-in-production"
            ),
            debug=self._get_config_value(
                "DEBUG",
                config_parser,
                "app",
                "debug",
                "False"
            ).lower() == "true"
        )
        
        # Create directories if they don't exist
        self._ensure_directories_exist()
        
        # Validate configuration
        self._validate_configuration()
    
    def _get_config_value(self, env_var: str, config_parser: configparser.ConfigParser, 
                         section: str, key: str, default: str) -> str:
        """Get configuration value with precedence: env var > config file > default"""
        # Check environment variable first
        value = os.getenv(env_var)
        if value is not None:
            return value
        
        # Check config file
        try:
            if config_parser.has_section(section) and config_parser.has_option(section, key):
                return config_parser.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass
        
        # Return default
        return default
    
    def _get_list_config_value(self, env_var: str, config_parser: configparser.ConfigParser,
                              section: str, key: str, default: List[str]) -> List[str]:
        """Get list configuration value"""
        value = self._get_config_value(env_var, config_parser, section, key, "")
        if value:
            return [item.strip() for item in value.split(",")]
        return default
    
    def _ensure_directories_exist(self) -> None:
        """Create necessary directories if they don't exist"""
        directories = [
            self._config.upload_directory,
            self._config.reports_directory,
            self._config.model_directory.parent  # Ensure parent directory exists
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise
    
    def _validate_configuration(self) -> None:
        """Validate configuration values"""
        errors = []
        warnings = []
        
        # Validate file size
        if self._config.max_file_size <= 0:
            errors.append("max_file_size must be positive")
        
        # Validate thresholds
        if not (0.0 <= self._config.face_detection_threshold <= 1.0):
            errors.append("face_detection_threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= self._config.recognition_threshold <= 1.0):
            errors.append("recognition_threshold must be between 0.0 and 1.0")
        
        # Validate file types
        if not self._config.allowed_file_types:
            warnings.append("No allowed file types specified")
        
        # Validate secret key
        if self._config.secret_key == "dev-secret-key-change-in-production":
            warnings.append("Using default secret key - change in production!")
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
        
        # Raise errors
        if errors:
            error_msg = "Configuration errors: " + "; ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @property
    def config(self) -> SystemConfig:
        """Get the current configuration"""
        return self._config
    
    def get_database_url(self) -> str:
        """Get database URL"""
        return self._config.database_url
    
    def get_upload_directory(self) -> Path:
        """Get upload directory path"""
        return self._config.upload_directory
    
    def get_model_directory(self) -> Path:
        """Get model directory path"""
        return self._config.model_directory
    
    def get_reports_directory(self) -> Path:
        """Get reports directory path"""
        return self._config.reports_directory
    
    def get_allowed_file_types(self) -> List[str]:
        """Get allowed file types"""
        return self._config.allowed_file_types
    
    def get_max_file_size(self) -> int:
        """Get maximum file size in bytes"""
        return self._config.max_file_size
    
    def get_face_detection_threshold(self) -> float:
        """Get face detection threshold"""
        return self._config.face_detection_threshold
    
    def get_recognition_threshold(self) -> float:
        """Get face recognition threshold"""
        return self._config.recognition_threshold
    
    def reload_configuration(self) -> None:
        """Reload configuration from sources"""
        logger.info("Reloading configuration")
        self._load_configuration()


# Global configuration manager instance
config_manager = ConfigurationManager()