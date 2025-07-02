import os
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    provider: str = "local"  # local, sharepoint, google_drive, aws_s3, azure_files
    refresh_interval_minutes: int = 60
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

@dataclass
class AppConfig:
    """Main application configuration"""
    # Flask settings
    secret_key: str = os.getenv('SECRET_KEY', 'basketball_dashboard_secret_key')
    debug: bool = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port: int = int(os.getenv('PORT', 5000))
    host: str = os.getenv('HOST', '0.0.0.0')
    
    # Environment
    environment: str = os.getenv('ENVIRONMENT', 'development')
    
    # Security
    allowed_origins: list = None
    rate_limit: str = os.getenv('RATE_LIMIT', '100 per hour')
    
    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_to_file: bool = os.getenv('LOG_TO_FILE', 'False').lower() == 'true'
    
    # AWS/Cloud settings
    aws_region: str = os.getenv('AWS_REGION', 'us-east-1')
    
    # Data source configuration
    database: DatabaseConfig = None
    
    # Performance optimization for cost reduction
    cache_timeout: int = int(os.getenv('CACHE_TIMEOUT', 86400))  # 24 hours default
    enable_data_caching: bool = os.getenv('ENABLE_CACHING', 'True').lower() == 'true'
    
    # Cost optimization settings
    lazy_load_map: bool = os.getenv('LAZY_LOAD_MAP', 'True').lower() == 'true'
    reduce_memory_usage: bool = os.getenv('REDUCE_MEMORY', 'True').lower() == 'true'
    
    def __post_init__(self):
        if self.allowed_origins is None:
            origins = os.getenv('ALLOWED_ORIGINS', '*')
            self.allowed_origins = [origin.strip() for origin in origins.split(',')]
        
        if self.database is None:
            self.database = self._get_database_config()
    
    def _get_database_config(self) -> DatabaseConfig:
        """Get database configuration based on environment variables"""
        provider = os.getenv('DATA_PROVIDER', 'local')
        
        config = {}
        
        if provider == 'sharepoint':
            config = {
                'site_url': os.getenv('SHAREPOINT_SITE_URL'),
                'file_path': os.getenv('SHAREPOINT_FILE_PATH'),
                'client_id': os.getenv('SHAREPOINT_CLIENT_ID'),
                'client_secret': os.getenv('SHAREPOINT_CLIENT_SECRET'),
                'tenant_id': os.getenv('SHAREPOINT_TENANT_ID')
            }
        elif provider == 'google_drive':
            config = {
                'file_id': os.getenv('GOOGLE_DRIVE_FILE_ID'),
                'credentials_path': os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
            }
        elif provider == 'aws_s3':
            config = {
                'bucket': os.getenv('S3_BUCKET'),
                'key': os.getenv('S3_KEY'),
                'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
                'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'region': os.getenv('AWS_REGION', 'us-east-1')
            }
        elif provider == 'azure_files':
            config = {
                'account_name': os.getenv('AZURE_STORAGE_ACCOUNT'),
                'account_key': os.getenv('AZURE_STORAGE_KEY'),
                'share_name': os.getenv('AZURE_SHARE_NAME'),
                'file_path': os.getenv('AZURE_FILE_PATH')
            }
        
        return DatabaseConfig(
            provider=provider,
            refresh_interval_minutes=int(os.getenv('DATA_REFRESH_INTERVAL', 60)),
            config=config
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == 'development'

def get_config() -> AppConfig:
    """Get application configuration based on environment"""
    return AppConfig()

def load_country_coordinates() -> Dict[str, list]:
    """Load country coordinates from JSON file"""
    try:
        with open('data/country_coordinates.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to empty dict if file not found
        return {}

# Global configuration instance
config = get_config() 