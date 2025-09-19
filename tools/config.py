"""
Configuration management for Bible XML importer.

This module handles all configuration settings including Azure connections,
database settings, and application parameters.
"""

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus


@dataclass
class AzureConfig:
    """Azure-related configuration settings."""
    
    # Blob Storage
    storage_account_name: str
    storage_account_key: Optional[str] = None
    storage_connection_string: Optional[str] = None
    blob_container_name: str = "bible-translations"
    
    # Authentication - prefer managed identity in production
    use_managed_identity: bool = True
    
    def get_blob_service_url(self) -> str:
        """Get the blob service URL."""
        return f"https://{self.storage_account_name}.blob.core.windows.net"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    
    server: str
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    driver: str = "ODBC Driver 18 for SQL Server"
    
    # Connection pool settings
    connection_timeout: int = 30
    command_timeout: int = 300
    pool_size: int = 5
    
    # Batch processing settings
    batch_size: int = 2000
    max_retries: int = 3
    retry_delay: float = 1.0
    skip_existing: bool = True  # Added for duplicate handling
    
    # Use Azure AD authentication if no username/password provided
    use_azure_ad: bool = True
    
    def get_connection_string(self) -> str:
        """Generate the database connection string."""
        base_params = {
            "DRIVER": self.driver,
            "SERVER": self.server,
            "DATABASE": self.database,
            "Encrypt": "yes",
            "TrustServerCertificate": "no",
            "Connection Timeout": str(self.connection_timeout),
        }
        
        if self.username and self.password:
            # SQL authentication
            base_params.update({
                "UID": self.username,
                "PWD": self.password
            })
        elif self.use_azure_ad:
            # Azure AD authentication
            base_params["Authentication"] = "ActiveDirectoryMsi"
        else:
            # Windows authentication (for local development)
            base_params["Trusted_Connection"] = "yes"
        
        return ";".join(f"{k}={v}" for k, v in base_params.items())


@dataclass
class ImporterConfig:
    """Main importer configuration settings."""
    
    # Processing settings
    dry_run: bool = False
    skip_existing: bool = True
    show_progress: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # XML parsing settings
    streaming_threshold_mb: int = 100  # Use streaming for files larger than this
    memory_limit_mb: int = 500  # Memory usage limit
    
    # Error handling
    continue_on_error: bool = False
    max_errors: int = 100


class Config:
    """Main configuration class that combines all settings."""
    
    def __init__(self):
        self.azure = self._load_azure_config()
        self.database = self._load_database_config()
        self.importer = self._load_importer_config()
    
    def _load_azure_config(self) -> AzureConfig:
        """Load Azure configuration from environment variables."""
        storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        if not storage_account_name:
            raise ValueError("AZURE_STORAGE_ACCOUNT_NAME environment variable is required")
        
        return AzureConfig(
            storage_account_name=storage_account_name,
            storage_account_key=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
            storage_connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
            blob_container_name=os.getenv("AZURE_BLOB_CONTAINER_NAME", "bible-translations"),
            use_managed_identity=os.getenv("AZURE_USE_MANAGED_IDENTITY", "true").lower() == "true"
        )
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables."""
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_DATABASE")
        
        if not server or not database:
            raise ValueError("DB_SERVER and DB_DATABASE environment variables are required")
        
        return DatabaseConfig(
            server=server,
            database=database,
            username=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
            driver=os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server"),
            connection_timeout=int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
            command_timeout=int(os.getenv("DB_COMMAND_TIMEOUT", "300")),
            batch_size=int(os.getenv("DB_BATCH_SIZE", "2000")),
            max_retries=int(os.getenv("DB_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("DB_RETRY_DELAY", "1.0")),
            skip_existing=os.getenv("DB_SKIP_EXISTING", "true").lower() == "true",
            use_azure_ad=os.getenv("DB_USE_AZURE_AD", "true").lower() == "true"
        )
    
    def _load_importer_config(self) -> ImporterConfig:
        """Load importer configuration from environment variables."""
        return ImporterConfig(
            dry_run=os.getenv("IMPORTER_DRY_RUN", "false").lower() == "true",
            skip_existing=os.getenv("IMPORTER_SKIP_EXISTING", "true").lower() == "true",
            show_progress=os.getenv("IMPORTER_SHOW_PROGRESS", "true").lower() == "true",
            log_level=os.getenv("IMPORTER_LOG_LEVEL", "INFO").upper(),
            log_file=os.getenv("IMPORTER_LOG_FILE"),
            streaming_threshold_mb=int(os.getenv("IMPORTER_STREAMING_THRESHOLD_MB", "100")),
            memory_limit_mb=int(os.getenv("IMPORTER_MEMORY_LIMIT_MB", "500")),
            continue_on_error=os.getenv("IMPORTER_CONTINUE_ON_ERROR", "false").lower() == "true",
            max_errors=int(os.getenv("IMPORTER_MAX_ERRORS", "100"))
        )
    
    def validate(self) -> None:
        """Validate the configuration settings."""
        # Validate Azure config
        if not self.azure.storage_account_name:
            raise ValueError("Azure storage account name is required")
        
        if not self.azure.use_managed_identity and not (
            self.azure.storage_account_key or self.azure.storage_connection_string
        ):
            raise ValueError("Azure storage key or connection string required when not using managed identity")
        
        # Validate database config
        if not self.database.server or not self.database.database:
            raise ValueError("Database server and database name are required")
        
        if not self.database.use_azure_ad and not (self.database.username and self.database.password):
            raise ValueError("Database credentials required when not using Azure AD authentication")
        
        # Validate importer config
        if self.database.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        
        if self.database.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


# Global configuration instance
config = Config()