"""Jira service for MCP integration"""

from typing import Any, Dict, List, Optional, Tuple

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from ..base_service import BaseMCPService
from ..credentials import ServiceCredential
from ...utils.logging import get_logger

logger = get_logger(__name__)


class JiraService(BaseMCPService):
    """Jira integration service"""
    
    def __init__(self, name: str, config: Dict[str, Any], credentials: Optional[ServiceCredential] = None):
        super().__init__(name, config, credentials)
        
        self.base_url = config.get('url', '')
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        # API version detection (v2 or v3)
        # If not specified, will detect during connect()
        self.api_version = config.get('api_version', None)
        self.detected_version = None
        self.session = None
    
    async def connect(self) -> Tuple[bool, Optional[str]]:
        """Connect to Jira"""
        try:
            if not self.base_url:
                return False, "Jira URL not configured"
            
            # Detect API version if not specified (per FR-038)
            if not self.api_version:
                self.detected_version = await self._detect_api_version()
                logger.info(f"Detected Jira API version: {self.detected_version}")
            else:
                self.detected_version = self.api_version
            
            # Stub implementation - actual aiohttp session creation would go here
            if AIOHTTP_AVAILABLE:
                # Would create aiohttp.ClientSession() here in real implementation
                pass
            
            self.connected = True
            logger.info(f"Connected to Jira at {self.base_url} (API v{self.detected_version})")
            return True, None
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            return False, str(e)
    
    async def _detect_api_version(self) -> str:
        """Detect Jira API version (v2 or v3)"""
        # Stub implementation - in real version would check /rest/api/2/serverInfo
        # and /rest/api/3/serverInfo to determine available versions
        # Default to v2 for backward compatibility
        return "2"
    
    async def disconnect(self) -> Tuple[bool, Optional[str]]:
        """Disconnect from Jira"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            self.connected = False
            logger.info("Disconnected from Jira")
            return True, None
        except Exception as e:
            logger.error(f"Failed to disconnect from Jira: {e}")
            return False, str(e)
    
    async def authenticate(self) -> Tuple[bool, Optional[str]]:
        """Authenticate with Jira"""
        try:
            if not self.credentials:
                return False, "No credentials provided"
            
            # For now, just validate credentials exist
            # In real implementation, would make test API call
            if self.credentials.api_token or (self.credentials.username and self.credentials.password):
                logger.info("Jira authentication successful (stub)")
                return True, None
            else:
                return False, "Invalid credentials: need api_token or username+password"
        except Exception as e:
            logger.error(f"Jira authentication failed: {e}")
            return False, str(e)
    
    async def health_check(self) -> Tuple[bool, Optional[str]]:
        """Check Jira health"""
        try:
            if not self.session:
                return False, "Not connected"
            
            # Stub implementation - in real version would call /rest/api/2/serverInfo
            logger.info("Jira health check passed (stub)")
            return True, None
        except Exception as e:
            logger.error(f"Jira health check failed: {e}")
            return False, str(e)
    
    async def list_issues(self, jql: str = "", max_results: int = 50) -> Tuple[bool, Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        List Jira issues using JQL query
        Returns: (success, issues, error_message)
        """
        try:
            if not self.connected:
                return False, None, "Not connected to Jira"
            
            # Stub implementation
            logger.info(f"Listing Jira issues with JQL: {jql} (stub)")
            stub_issues = [
                {'key': 'PROJ-1', 'summary': 'Example issue', 'status': 'Open'},
                {'key': 'PROJ-2', 'summary': 'Another issue', 'status': 'In Progress'}
            ]
            return True, stub_issues, None
        except Exception as e:
            logger.error(f"Failed to list issues: {e}")
            return False, None, str(e)
    
    async def get_issue(self, issue_key: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Get a specific Jira issue
        Returns: (success, issue_data, error_message)
        """
        try:
            if not self.connected:
                return False, None, "Not connected to Jira"
            
            # Stub implementation
            logger.info(f"Getting Jira issue {issue_key} (stub)")
            stub_issue = {
                'key': issue_key,
                'summary': 'Example issue',
                'description': 'This is a stub issue',
                'status': 'Open'
            }
            return True, stub_issue, None
        except Exception as e:
            logger.error(f"Failed to get issue {issue_key}: {e}")
            return False, None, str(e)
    
    async def create_issue(self, project_key: str, summary: str, description: str = "", 
                          issue_type: str = "Task") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a new Jira issue
        Returns: (success, issue_key, error_message)
        """
        try:
            if not self.connected:
                return False, None, "Not connected to Jira"
            
            # Stub implementation
            logger.info(f"Creating Jira issue in {project_key}: {summary} (stub)")
            stub_key = f"{project_key}-123"
            return True, stub_key, None
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return False, None, str(e)
    
    async def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Update a Jira issue
        Returns: (success, error_message)
        """
        try:
            if not self.connected:
                return False, "Not connected to Jira"
            
            # Stub implementation
            logger.info(f"Updating Jira issue {issue_key} with fields: {fields} (stub)")
            return True, None
        except Exception as e:
            logger.error(f"Failed to update issue {issue_key}: {e}")
            return False, str(e)
