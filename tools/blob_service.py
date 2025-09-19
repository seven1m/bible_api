"""
Azure Blob Storage service for Bible XML importer.

This module provides functionality to download XML files from Azure Blob Storage
with proper authentication, error handling, and progress tracking.
"""

import io
import logging
from typing import Optional, List, Dict, Callable
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import AzureError, ResourceNotFoundError

from .config import AzureConfig


logger = logging.getLogger(__name__)


class BlobStorageService:
    """Service for downloading files from Azure Blob Storage."""
    
    def __init__(self, config: AzureConfig):
        """
        Initialize the blob storage service.
        
        Args:
            config: Azure configuration settings
        """
        self.config = config
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Set up the blob service client with appropriate authentication."""
        try:
            if self.config.storage_connection_string:
                # Use connection string if provided
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    self.config.storage_connection_string
                )
                logger.info("Initialized blob client with connection string")
                
            elif self.config.use_managed_identity:
                # Use managed identity for authentication
                try:
                    from azure.identity import DefaultAzureCredential
                    credential = DefaultAzureCredential()
                    account_url = self.config.get_blob_service_url()
                    self._blob_service_client = BlobServiceClient(
                        account_url=account_url,
                        credential=credential
                    )
                    logger.info("Initialized blob client with managed identity")
                except ImportError:
                    logger.warning("azure-identity package not available, falling back to storage key")
                    if not self.config.storage_account_key:
                        raise ValueError("azure-identity not available and no storage key provided")
                    # Fall through to storage key authentication
                
            if self._blob_service_client is None and self.config.storage_account_key:
                # Use storage account key
                account_url = self.config.get_blob_service_url()
                self._blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.config.storage_account_key
                )
                logger.info("Initialized blob client with storage account key")
                
            if self._blob_service_client is None:
                raise ValueError("No valid authentication method configured for blob storage")
                
        except Exception as e:
            logger.error(f"Failed to initialize blob service client: {e}")
            raise
    
    @property
    def client(self) -> BlobServiceClient:
        """Get the blob service client, ensuring it's properly initialized."""
        if self._blob_service_client is None:
            raise RuntimeError("Blob service client not initialized")
        return self._blob_service_client
    
    def blob_exists(self, blob_name: str) -> bool:
        """
        Check if a blob exists in the container.
        
        Args:
            blob_name: Name of the blob to check
            
        Returns:
            True if the blob exists, False otherwise
        """
        try:
            blob_client = self._blob_service_client.get_blob_client(
                container=self.config.blob_container_name,
                blob=blob_name
            )
            blob_client.get_blob_properties()
            return True
            
        except ResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking if blob '{blob_name}' exists: {e}")
            raise
    
    def get_blob_size(self, blob_name: str) -> int:
        """
        Get the size of a blob in bytes.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Size of the blob in bytes
            
        Raises:
            ResourceNotFoundError: If the blob doesn't exist
        """
        try:
            blob_client = self.client.get_blob_client(
                container=self.config.blob_container_name,
                blob=blob_name
            )
            properties = blob_client.get_blob_properties()
            return properties.size
            
        except Exception as e:
            logger.error(f"Error getting size of blob '{blob_name}': {e}")
            raise
    
    def download_blob_to_stream(self, blob_name: str) -> io.BytesIO:
        """
        Download a blob to a memory stream.
        
        Args:
            blob_name: Name of the blob to download
            
        Returns:
            BytesIO stream containing the blob data
            
        Raises:
            ResourceNotFoundError: If the blob doesn't exist
            AzureError: For other Azure-related errors
        """
        try:
            if not self.blob_exists(blob_name):
                raise ResourceNotFoundError(f"Blob '{blob_name}' not found")
            
            logger.info(f"Downloading blob '{blob_name}' to memory stream")
            
            blob_client = self.client.get_blob_client(
                container=self.config.blob_container_name,
                blob=blob_name
            )
            
            # Download to memory stream
            stream = io.BytesIO()
            download_stream = blob_client.download_blob()
            download_stream.readinto(stream)
            stream.seek(0)
            
            size_mb = len(stream.getvalue()) / (1024 * 1024)
            logger.info(f"Successfully downloaded blob '{blob_name}' ({size_mb:.2f} MB)")
            
            return stream
            
        except ResourceNotFoundError:
            logger.error(f"Blob '{blob_name}' not found in container '{self.config.blob_container_name}'")
            raise
        except AzureError as e:
            logger.error(f"Azure error downloading blob '{blob_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading blob '{blob_name}': {e}")
            raise
    
    def download_blob_with_progress(self, blob_name: str, progress_callback=None) -> io.BytesIO:
        """
        Download a blob with progress tracking.
        
        Args:
            blob_name: Name of the blob to download
            progress_callback: Optional callback function to track progress
                             Should accept (bytes_downloaded, total_bytes) parameters
            
        Returns:
            BytesIO stream containing the blob data
        """
        try:
            if not self.blob_exists(blob_name):
                raise ResourceNotFoundError(f"Blob '{blob_name}' not found")
            
            # Get blob size for progress tracking
            total_size = self.get_blob_size(blob_name)
            logger.info(f"Downloading blob '{blob_name}' ({total_size / (1024*1024):.2f} MB)")
            
            blob_client = self.client.get_blob_client(
                container=self.config.blob_container_name,
                blob=blob_name
            )
            
            # Download with progress tracking
            stream = io.BytesIO()
            bytes_downloaded = 0
            
            download_stream = blob_client.download_blob()
            
            # Read in chunks for progress tracking
            chunk_size = 1024 * 1024  # 1MB chunks
            for chunk in download_stream.chunks():
                stream.write(chunk)
                bytes_downloaded += len(chunk)
                
                if progress_callback:
                    progress_callback(bytes_downloaded, total_size)
            
            stream.seek(0)
            logger.info(f"Successfully downloaded blob '{blob_name}'")
            
            return stream
            
        except Exception as e:
            logger.error(f"Error downloading blob '{blob_name}' with progress: {e}")
            raise
    
    def list_blobs(self, prefix: str = "") -> List[str]:
        """
        List all blobs in the container with an optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter blob names
            
        Returns:
            List of blob names
        """
        try:
            container_client = self.client.get_container_client(
                self.config.blob_container_name
            )
            
            blob_names = []
            for blob in container_client.list_blobs(name_starts_with=prefix):
                blob_names.append(blob.name)
            
            logger.info(f"Found {len(blob_names)} blobs with prefix '{prefix}'")
            return blob_names
            
        except Exception as e:
            logger.error(f"Error listing blobs with prefix '{prefix}': {e}")
            raise
    
    def get_blob_metadata(self, blob_name: str) -> Dict:
        """
        Get metadata for a specific blob.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Dictionary containing blob metadata
        """
        try:
            blob_client = self.client.get_blob_client(
                container=self.config.blob_container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                "name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type,
                "etag": properties.etag,
                "metadata": properties.metadata or {}
            }
            
        except Exception as e:
            logger.error(f"Error getting metadata for blob '{blob_name}': {e}")
            raise