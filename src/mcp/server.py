"""Embedded MCP server for managing external integrations"""

import asyncio
import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .credentials import CredentialStore, ServiceCredential
from .base_service import BaseMCPService
from .services import (
    JiraService, GitHubService, DatabaseService,
    TerminalService, ChromeService, GitService
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


def compute_params_hash(params: Dict[str, Any]) -> str:
    """Compute stable hash of request parameters for cache lookup"""
    # Sort parameters to ensure consistent hash
    sorted_params = json.dumps(params, sort_keys=True)
    return hashlib.md5(sorted_params.encode()).hexdigest()



class ServiceType(Enum):
    """Supported MCP service types"""
    JIRA = "jira"
    GITHUB = "github"
    GIT = "git"
    DATABASE = "database"
    TERMINAL = "terminal"
    CHROME = "chrome"


class ConnectionState(Enum):
    """Connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPConnection:
    """Represents an MCP service connection"""
    service_type: ServiceType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    state: ConnectionState = ConnectionState.DISCONNECTED
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'service_type': self.service_type.value,
            'name': self.name,
            'config': self.config,
            'state': self.state.value,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPConnection':
        """Create from dictionary"""
        return cls(
            service_type=ServiceType(data['service_type']),
            name=data['name'],
            config=data.get('config', {}),
            state=ConnectionState(data.get('state', 'disconnected')),
            error_message=data.get('error_message')
        )


@dataclass
class CachedResponse:
    """Represents a cached MCP service response for offline support"""
    service_type: ServiceType
    service_name: str
    method: str  # e.g., "list_issues", "get_repository"
    params_hash: str  # Hash of request parameters for lookup
    response_data: Dict[str, Any]
    timestamp: datetime
    ttl_hours: int = 24  # Time-to-live in hours
    
    def is_expired(self) -> bool:
        """Check if cached response has expired"""
        expiry_time = self.timestamp + timedelta(hours=self.ttl_hours)
        return datetime.now() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'service_type': self.service_type.value,
            'service_name': self.service_name,
            'method': self.method,
            'params_hash': self.params_hash,
            'response_data': json.dumps(self.response_data),
            'timestamp': self.timestamp.isoformat(),
            'ttl_hours': self.ttl_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CachedResponse':
        """Create from database dictionary"""
        return cls(
            service_type=ServiceType(data['service_type']),
            service_name=data['service_name'],
            method=data['method'],
            params_hash=data['params_hash'],
            response_data=json.loads(data['response_data']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            ttl_hours=data.get('ttl_hours', 24)
        )


class EmbeddedMCPServer:
    """Embedded MCP server running in separate thread"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.connections: Dict[str, MCPConnection] = {}
        self.config_file = cache_dir / "mcp_connections.json"
        
        # Credential store
        self.credential_store = CredentialStore()
        
        # Response cache database
        self.cache_db_path = cache_dir / "mcp_cache.db"
        self._init_cache_database()
        self._offline_mode = False
        
        # Event loop and thread
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        logger.debug("EmbeddedMCPServer initialized")
    
    def _init_cache_database(self) -> None:
        """Initialize SQLite cache database"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Create cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS response_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    method TEXT NOT NULL,
                    params_hash TEXT NOT NULL,
                    response_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ttl_hours INTEGER DEFAULT 24,
                    UNIQUE(service_type, service_name, method, params_hash)
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_lookup
                ON response_cache(service_type, service_name, method, params_hash)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.debug("Cache database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")
    
    def is_offline(self) -> bool:
        """Check if running in offline mode"""
        return self._offline_mode
    
    def set_offline_mode(self, offline: bool) -> None:
        """Set offline mode (for testing or when network unavailable)"""
        self._offline_mode = offline
        logger.info(f"Offline mode: {'enabled' if offline else 'disabled'}")
    
    def cache_response(self, cached: CachedResponse) -> None:
        """Store a service response in cache"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            data = cached.to_dict()
            
            # Insert or replace existing cache entry
            cursor.execute('''
                INSERT OR REPLACE INTO response_cache
                (service_type, service_name, method, params_hash, response_data, timestamp, ttl_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['service_type'],
                data['service_name'],
                data['method'],
                data['params_hash'],
                data['response_data'],
                data['timestamp'],
                data['ttl_hours']
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Cached response for {cached.service_name}.{cached.method}")
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
    
    def get_cached_response(
        self, 
        service_type: ServiceType, 
        service_name: str, 
        method: str, 
        params_hash: str
    ) -> Optional[CachedResponse]:
        """Retrieve cached response if available and not expired"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT service_type, service_name, method, params_hash, 
                       response_data, timestamp, ttl_hours
                FROM response_cache
                WHERE service_type = ? AND service_name = ? 
                      AND method = ? AND params_hash = ?
            ''', (service_type.value, service_name, method, params_hash))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Reconstruct cached response
            cached = CachedResponse.from_dict({
                'service_type': row[0],
                'service_name': row[1],
                'method': row[2],
                'params_hash': row[3],
                'response_data': row[4],
                'timestamp': row[5],
                'ttl_hours': row[6]
            })
            
            # Check if expired
            if cached.is_expired():
                logger.debug(f"Cached response expired for {service_name}.{method}")
                return None
            
            logger.debug(f"Retrieved cached response for {service_name}.{method}")
            return cached
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached response: {e}")
            return None
    
    def clear_expired_cache(self) -> int:
        """Remove expired cache entries and return count deleted"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Load all entries and check expiration
            cursor.execute('SELECT id, timestamp, ttl_hours FROM response_cache')
            rows = cursor.fetchall()
            
            expired_ids = []
            for row_id, timestamp_str, ttl_hours in rows:
                timestamp = datetime.fromisoformat(timestamp_str)
                expiry_time = timestamp + timedelta(hours=ttl_hours)
                if datetime.now() > expiry_time:
                    expired_ids.append(row_id)
            
            # Delete expired entries
            if expired_ids:
                placeholders = ','.join('?' * len(expired_ids))
                cursor.execute(f'DELETE FROM response_cache WHERE id IN ({placeholders})', expired_ids)
                conn.commit()
            
            conn.close()
            
            if expired_ids:
                logger.info(f"Cleared {len(expired_ids)} expired cache entries")
            
            return len(expired_ids)
            
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0
    
    def start(self) -> bool:
        """Start MCP server in background thread"""
        if self.running:
            logger.warning("MCP server already running")
            return True
        
        try:
            logger.info("Starting MCP server...")
            
            # Create event loop in separate thread
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
            
            # Wait for loop to be ready (max 3s per FR-042)
            import time
            timeout = 3.0
            start_time = time.time()
            
            while self.loop is None and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.loop is None:
                logger.error("MCP server failed to start within 3s timeout")
                return False
            
            self.running = True
            
            # Load saved connections
            self._load_connections()
            
            logger.info("MCP server started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    def stop(self) -> None:
        """Stop MCP server"""
        if not self.running:
            return
        
        logger.info("Stopping MCP server...")
        
        self.running = False
        
        # Stop event loop
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("MCP server stopped")
    
    def _run_event_loop(self) -> None:
        """Run asyncio event loop in thread"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            logger.debug("MCP event loop started")
            self.loop.run_forever()
            logger.debug("MCP event loop stopped")
            
        except Exception as e:
            logger.error(f"MCP event loop error: {e}")
        finally:
            if self.loop:
                self.loop.close()
    
    def add_connection(self, connection: MCPConnection) -> bool:
        """Add a new connection"""
        try:
            self.connections[connection.name] = connection
            self._save_connections()
            logger.info(f"Added connection: {connection.name} ({connection.service_type.value})")
            return True
        except Exception as e:
            logger.error(f"Failed to add connection: {e}")
            return False
    
    def remove_connection(self, name: str) -> bool:
        """Remove a connection"""
        try:
            if name in self.connections:
                del self.connections[name]
                self._save_connections()
                logger.info(f"Removed connection: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove connection: {e}")
            return False
    
    def get_connection(self, name: str) -> Optional[MCPConnection]:
        """Get connection by name"""
        return self.connections.get(name)
    
    def list_connections(self) -> List[MCPConnection]:
        """List all connections"""
        return list(self.connections.values())
    
    def test_connection(self, name: str) -> tuple[bool, Optional[str]]:
        """Test a connection using the actual service"""
        connection = self.get_connection(name)
        
        if not connection:
            return False, "Connection not found"
        
        # Set state to connecting
        connection.state = ConnectionState.CONNECTING
        
        # Get credentials
        credentials = self.credential_store.get_credentials(name)
        
        # Create service instance
        service = self._create_service(connection, credentials)
        if not service:
            connection.state = ConnectionState.ERROR
            connection.error_message = f"Unsupported service type: {connection.service_type.value}"
            return False, connection.error_message
        
        # Run async test in the event loop
        if not self.loop:
            connection.state = ConnectionState.ERROR
            connection.error_message = "MCP server not running"
            return False, connection.error_message
        
        try:
            # Schedule the test in the event loop
            future = asyncio.run_coroutine_threadsafe(
                service.test_connection(),
                self.loop
            )
            
            # Wait for result with timeout (5s per FR-014)
            success, error = future.result(timeout=5.0)
            
            # Update connection state
            if success:
                connection.state = ConnectionState.CONNECTED
                connection.error_message = None
                logger.info(f"Connection test successful: {name}")
            else:
                connection.state = ConnectionState.ERROR
                connection.error_message = error or "Connection test failed"
                logger.warning(f"Connection test failed for {name}: {error}")
            
            return success, error
            
        except asyncio.TimeoutError:
            error_msg = "Connection timeout after 5 seconds"
            logger.error(f"Connection test timeout for {name}")
            connection.state = ConnectionState.ERROR
            connection.error_message = error_msg
            return False, error_msg
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Connection test failed for {name}: {e}")
            connection.state = ConnectionState.ERROR
            connection.error_message = error_msg
            return False, error_msg
    
    def _create_service(self, connection: MCPConnection, credentials: Optional[ServiceCredential]) -> Optional[BaseMCPService]:
        """Create a service instance based on connection type"""
        service_classes = {
            ServiceType.JIRA: JiraService,
            ServiceType.GITHUB: GitHubService,
            ServiceType.GIT: GitService,
            ServiceType.DATABASE: DatabaseService,
            ServiceType.TERMINAL: TerminalService,
            ServiceType.CHROME: ChromeService,
        }
        
        service_class = service_classes.get(connection.service_type)
        if service_class:
            return service_class(connection.name, connection.config, credentials)
        return None
    
    def _save_connections(self) -> None:
        """Save connections to file (excluding credentials)"""
        try:
            data = {
                name: conn.to_dict()
                for name, conn in self.connections.items()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(data)} connections to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save connections: {e}")
    
    def _load_connections(self) -> None:
        """Load connections from file"""
        if not self.config_file.exists():
            logger.debug("No saved connections found")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            self.connections = {
                name: MCPConnection.from_dict(conn_data)
                for name, conn_data in data.items()
            }
            
            logger.info(f"Loaded {len(self.connections)} connections")
            
        except Exception as e:
            logger.error(f"Failed to load connections: {e}")
