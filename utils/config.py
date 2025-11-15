"""
Configuration module using Pydantic Settings.

This module implements a robust configuration system using pydantic-settings
for automatic validation, type checking, and environment variable loading.
It uses the Singleton pattern to ensure a single configuration instance
throughout the application lifecycle.
"""

from typing import Literal, ClassVar
from pathlib import Path
from pydantic import Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic._internal._model_construction import ModelMetaclass


class SingletonSettingsMeta(ModelMetaclass):
    """
    Metaclass implementing the Singleton pattern with class-level attribute access.

    This metaclass:
    1. Ensures only one instance of a class can exist
    2. Allows accessing instance attributes as class attributes
    3. Provides a reset mechanism for testing

    Example:
        class MySettings(BaseSettings, metaclass=SingletonMeta):
            api_url: str

        # Access as class attribute
        url = MySettings.api_url

        # Or as instance attribute
        settings = MySettings()
        url = settings.api_url
    """

    _instances: ClassVar[dict[type, object]] = {}

    def __call__(cls, *args, **kwargs):
        """
        Control instance creation to enforce singleton behavior.

        :return: The singleton instance of the class
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

    def __getattribute__(cls, name: str):
        """
        Enable class-level attribute access to instance attributes.

        This allows accessing Settings.API_BASE_URL as a class attribute,
        which delegates to the singleton instance.

        :param name: Attribute name
        :return: Attribute value from singleton instance or class
        """
        # First try to get class-level attributes (methods, etc.)
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass

        # If not found and an instance exists, try to get from instance
        if cls in cls._instances:
            instance = cls._instances[cls]
            if hasattr(instance, name):
                return getattr(instance, name)

        # If still not found, try to create instance and get attribute
        # This handles the case where Settings.ATTR is accessed before instantiation
        try:
            instance = cls()
            if hasattr(instance, name):
                return getattr(instance, name)
        except Exception:
            pass

        raise AttributeError(
            f"type object '{cls.__name__}' has no attribute '{name}'"
        )

    @classmethod
    def reset(mcs):
        """
        Reset all singleton instances.

        Useful for testing purposes to ensure clean state.
        """
        mcs._instances.clear()


class Settings(BaseSettings, metaclass=SingletonSettingsMeta):
    """
    Application configuration with automatic validation.

    This class uses pydantic-settings to load configuration from environment
    variables and .env files, providing automatic type conversion and validation.
    It implements the Singleton pattern via metaclass to ensure a single
    configuration instance exists throughout the application.

    Configuration sources (in order of priority):
    1. Environment variables
    2. .env file
    3. Default values

    :cvar API_BASE_URL: Base URL for the external joke API service
    :cvar MCP_SERVER_HOST: Host address for the MCP server
    :cvar MCP_SERVER_PORT: Port number for the MCP server
    :cvar LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :cvar LOG_FILE: Path to the log file
    :cvar LOG_ROTATION: Log file rotation size/time
    :cvar LOG_RETENTION: Log file retention period
    :cvar SESSION_TIMEOUT: Session timeout in seconds
    :cvar SESSION_CLEANUP_INTERVAL: Interval for cleaning up expired sessions
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        validate_default=True,
    )

    # API Configuration
    API_BASE_URL: str = Field(
        ...,
        description="Base URL for the external joke API service",
        json_schema_extra={"example": "https://official-joke-api.appspot.com"}
    )

    # Server Configuration
    MCP_SERVER_HOST: str = Field(
        default="0.0.0.0",
        description="Host address for the MCP server"
    )

    MCP_SERVER_PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port number for the MCP server (1-65535)"
    )

    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    LOG_FILE: str = Field(
        default="logs/mcp_server.log",
        description="Path to the log file"
    )

    LOG_ROTATION: str = Field(
        default="10 MB",
        description="Log file rotation size or time period"
    )

    LOG_RETENTION: str = Field(
        default="7 days",
        description="Log file retention period"
    )

    # Session Configuration
    SESSION_TIMEOUT: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Session timeout in seconds (60s - 24h)"
    )

    SESSION_CLEANUP_INTERVAL: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Interval for cleaning up expired sessions in seconds (60s - 1h)"
    )

    @field_validator("API_BASE_URL")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """
        Validate that the API base URL is a valid HTTP/HTTPS URL.

        :param v: The URL to validate
        :return: The validated URL (stripped of trailing slashes)
        :raises ValueError: If the URL is invalid
        """
        if not v:
            raise ValueError("API_BASE_URL cannot be empty")

        if not v.startswith(("http://", "https://")):
            raise ValueError("API_BASE_URL must start with http:// or https://")

        # Remove trailing slashes for consistency
        return v.rstrip("/")

    @field_validator("LOG_FILE")
    @classmethod
    def validate_log_file(cls, v: str) -> str:
        """
        Validate and ensure the log file directory exists.

        :param v: The log file path
        :return: The validated log file path
        """
        log_path = Path(v)

        # Create parent directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)

        return v

    @field_validator("LOG_ROTATION")
    @classmethod
    def validate_log_rotation(cls, v: str) -> str:
        """
        Validate log rotation format.

        Accepts formats like: "10 MB", "500 KB", "1 GB", "1 day", "1 week"

        :param v: The rotation value
        :return: The validated rotation value
        :raises ValueError: If the format is invalid
        """
        valid_size_units = ["KB", "MB", "GB"]
        valid_time_units = ["day", "days", "week", "weeks", "hour", "hours"]

        parts = v.strip().split()
        if len(parts) != 2:
            raise ValueError(
                f"LOG_ROTATION must be in format '<number> <unit>', got: {v}"
            )

        try:
            size_value = float(parts[0])
            if size_value <= 0:
                raise ValueError("Rotation value must be positive")
        except ValueError:
            raise ValueError(f"Invalid rotation value: {parts[0]}")

        unit = parts[1].upper()
        if unit not in valid_size_units and parts[1].lower() not in valid_time_units:
            raise ValueError(
                f"Invalid rotation unit: {parts[1]}. "
                f"Must be one of {valid_size_units} or {valid_time_units}"
            )

        return v

    @field_validator("LOG_RETENTION")
    @classmethod
    def validate_log_retention(cls, v: str) -> str:
        """
        Validate log retention format.

        Accepts formats like: "7 days", "2 weeks", "1 month"

        :param v: The retention value
        :return: The validated retention value
        :raises ValueError: If the format is invalid
        """
        valid_units = ["day", "days", "week", "weeks", "month", "months"]

        parts = v.strip().split()
        if len(parts) != 2:
            raise ValueError(
                f"LOG_RETENTION must be in format '<number> <unit>', got: {v}"
            )

        try:
            retention_value = int(parts[0])
            if retention_value <= 0:
                raise ValueError("Retention value must be positive")
        except ValueError:
            raise ValueError(f"Invalid retention value: {parts[0]}")

        if parts[1].lower() not in valid_units:
            raise ValueError(
                f"Invalid retention unit: {parts[1]}. Must be one of {valid_units}"
            )

        return v

    @classmethod
    def get_instance(cls) -> "Settings":
        """
        Get the singleton instance of Settings.

        This method provides an explicit way to access the singleton instance.

        :return: The Settings singleton instance
        """
        return cls()

    def model_dump_safe(self) -> dict[str, str]:
        """
        Return configuration as a dictionary with sensitive data masked.

        Useful for logging or debugging without exposing sensitive information.

        :return: Dictionary with configuration values
        """
        config_dict = self.model_dump()
        # In the future, mask sensitive fields here
        # For now, API_BASE_URL is not sensitive, but this method is ready
        return config_dict

    def __repr__(self) -> str:
        """
        Return a string representation of the configuration.

        :return: String representation
        """
        return (
            f"Settings("
            f"API_BASE_URL={self.API_BASE_URL!r}, "
            f"MCP_SERVER_HOST={self.MCP_SERVER_HOST!r}, "
            f"MCP_SERVER_PORT={self.MCP_SERVER_PORT}, "
            f"LOG_LEVEL={self.LOG_LEVEL!r}"
            f")"
        )