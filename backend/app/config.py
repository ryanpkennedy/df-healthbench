"""
Configuration module for DF HealthBench API.

This module uses Pydantic Settings to load and validate configuration
from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql://dfuser:dfpassword@localhost:5432/df_healthbench"
    
    # API Configuration
    api_title: str = "DF HealthBench API"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered medical document processing API"
    
    # Environment
    environment: Literal["development", "production", "test"] = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

