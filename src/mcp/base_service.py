"""Base class for MCP services"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from .credentials import ServiceCredential
from ..utils.logging import get_logger

logger = get_logger(__name__)


class BaseMCPService(ABC):
    """Abstract base class for all MCP services"""
    
    def __init__(self, name: str, config: Dict[str, Any], credentials: Optional[ServiceCredential] = None):
        self.name = name
        self.config = config
        self.credentials = credentials
        self.connected = False
        self.error_message: Optional[str] = None
    
    @abstractmethod
    async def connect(self) -> Tuple[bool, Optional[str]]:
        """
        Connect to the service
        Returns: (success: bool, error_message: Optional[str])
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> Tuple[bool, Optional[str]]:
        """
        Disconnect from the service
        Returns: (success: bool, error_message: Optional[str])
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Check if the service is healthy and accessible
        Returns: (healthy: bool, error_message: Optional[str])
        """
        pass
    
    @abstractmethod
    async def authenticate(self) -> Tuple[bool, Optional[str]]:
        """
        Authenticate with the service using credentials
        Returns: (success: bool, error_message: Optional[str])
        """
        pass
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test the connection by connecting, authenticating, and checking health
        Returns: (success: bool, error_message: Optional[str])
        """
        try:
            # Connect
            success, error = await self.connect()
            if not success:
                return False, f"Connection failed: {error}"
            
            # Authenticate
            success, error = await self.authenticate()
            if not success:
                await self.disconnect()
                return False, f"Authentication failed: {error}"
            
            # Health check
            success, error = await self.health_check()
            if not success:
                await self.disconnect()
                return False, f"Health check failed: {error}"
            
            # Disconnect after test
            await self.disconnect()
            
            return True, None
        except Exception as e:
            logger.error(f"Test connection failed for {self.name}: {e}")
            return False, str(e)
