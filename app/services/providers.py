"""Service provider helpers (similar to DI container factories)."""
from functools import lru_cache
from .azure_xml_service import AzureXMLBibleService

@lru_cache
def get_xml_service() -> AzureXMLBibleService:
    return AzureXMLBibleService()
