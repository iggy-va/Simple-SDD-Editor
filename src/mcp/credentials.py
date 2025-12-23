"""Secure credential storage using OS keyring"""

import json
from dataclasses import dataclass
from typing import Dict, Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from ..utils.logging import get_logger

logger = get_logger(__name__)

# Service name for keyring
KEYRING_SERVICE = "speckit-editor-mcp"


@dataclass
class ServiceCredential:
    """Credentials for an MCP service"""
    username: Optional[str] = None
    password: Optional[str] = None
    api_token: Optional[str] = None
    api_key: Optional[str] = None
    additional: Dict[str, str] = None
    
    def __post_init__(self):
        if self.additional is None:
            self.additional = {}
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        result = {}
        if self.username:
            result['username'] = self.username
        if self.password:
            result['password'] = self.password
        if self.api_token:
            result['api_token'] = self.api_token
        if self.api_key:
            result['api_key'] = self.api_key
        if self.additional:
            result.update(self.additional)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'ServiceCredential':
        """Create from dictionary"""
        return cls(
            username=data.get('username'),
            password=data.get('password'),
            api_token=data.get('api_token'),
            api_key=data.get('api_key'),
            additional={k: v for k, v in data.items() 
                       if k not in ['username', 'password', 'api_token', 'api_key']}
        )


class CredentialStore:
    """Manages secure credential storage"""
    
    def __init__(self):
        self.use_keyring = KEYRING_AVAILABLE
        if not self.use_keyring:
            logger.warning("keyring package not available - credentials will not be securely stored")
    
    def store_credentials(self, connection_name: str, credentials: ServiceCredential) -> bool:
        """Store credentials securely"""
        try:
            if self.use_keyring:
                # Store as JSON in keyring
                cred_json = json.dumps(credentials.to_dict())
                keyring.set_password(KEYRING_SERVICE, connection_name, cred_json)
                logger.info(f"Stored credentials for {connection_name} in keyring")
            else:
                logger.warning(f"Cannot securely store credentials for {connection_name} - keyring unavailable")
            return True
        except Exception as e:
            logger.error(f"Failed to store credentials for {connection_name}: {e}")
            return False
    
    def get_credentials(self, connection_name: str) -> Optional[ServiceCredential]:
        """Retrieve credentials"""
        try:
            if self.use_keyring:
                cred_json = keyring.get_password(KEYRING_SERVICE, connection_name)
                if cred_json:
                    cred_dict = json.loads(cred_json)
                    return ServiceCredential.from_dict(cred_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {connection_name}: {e}")
            return None
    
    def delete_credentials(self, connection_name: str) -> bool:
        """Delete credentials"""
        try:
            if self.use_keyring:
                keyring.delete_password(KEYRING_SERVICE, connection_name)
                logger.info(f"Deleted credentials for {connection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials for {connection_name}: {e}")
            return False
    
    def list_stored_connections(self) -> list[str]:
        """List connections with stored credentials"""
        # Note: keyring doesn't provide a way to list all keys
        # This would need to be tracked separately
        return []
