"""
Core configuration for FX Currency Conversion Microservice
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "FX Currency Conversion Service"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Refinitiv/Reuters Configuration
    refinitiv_client_id: Optional[str] = Field(default=None, alias="REFINITIV_CLIENT_ID")
    refinitiv_client_secret: Optional[str] = Field(default=None, alias="REFINITIV_CLIENT_SECRET")
    refinitiv_base_url: str = "https://api.refinitiv.com"
    refinitiv_token_url: str = "https://api.refinitiv.com/auth/oauth2/v1/token"
    
    # Cache Configuration
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    cache_ttl_seconds: int = 30
    cache_enabled: bool = True
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100
    
    # Logging
    log_level: str = "INFO"
    
    # Data paths
    data_dir: str = "app/data"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
