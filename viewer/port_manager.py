"""
Port Manager for Miktos Real-Time Viewer

Handles dynamic port allocation and conflict resolution to prevent
"address already in use" errors when starting multiple viewer instances.
"""

import socket
import logging
from typing import List, Tuple, Optional
import asyncio
import time


class PortManager:
    """
    Manages port allocation and availability checking for the Miktos platform
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('PortManager')
        
        # Default port ranges
        self.default_http_ports = [8080, 8090, 8100, 8110, 8120]
        self.default_ws_ports = [8081, 8091, 8101, 8111, 8121]
        
        # Reserved ports to avoid
        self.reserved_ports = {
            3000,   # Node.js development servers
            5000,   # Flask default
            8000,   # Django development server
            8888,   # Jupyter notebooks
            9000,   # Common development port
        }
        
        # Track allocated ports to avoid conflicts during rapid allocation
        self.allocated_ports = set()
    
    def is_port_available(self, port: int, host: str = "localhost") -> bool:
        """
        Check if a port is available for binding
        
        Args:
            port: Port number to check
            host: Host address to check (default: localhost)
            
        Returns:
            True if port is available, False otherwise
        """
        # First check IPv4
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    return False  # Port is in use
        except Exception as e:
            self.logger.debug(f"IPv4 check error for port {port}: {e}")
            return False
        
        # Also check IPv6 if available
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock6:
                sock6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = sock6.connect_ex((host, port))
                if result == 0:
                    return False  # Port is in use
        except Exception as e:
            # IPv6 might not be available, that's okay
            self.logger.debug(f"IPv6 check error for port {port}: {e}")
        
        # Try to actually bind to the port to ensure it's really available
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
                return True
        except OSError as e:
            self.logger.debug(f"Bind test failed for port {port}: {e}")
            return False
    
    def find_available_port(self, preferred_port: int, port_range: Optional[List[int]] = None) -> int:
        """
        Find an available port, starting with the preferred port
        
        Args:
            preferred_port: The port to try first
            port_range: List of ports to try if preferred is unavailable
            
        Returns:
            Available port number
            
        Raises:
            RuntimeError: If no available port is found
        """
        # Try preferred port first
        if preferred_port not in self.allocated_ports and self.is_port_available(preferred_port):
            self.logger.info(f"Using preferred port {preferred_port}")
            self.allocated_ports.add(preferred_port)
            return preferred_port
        
        self.logger.warning(f"Preferred port {preferred_port} is in use, searching for alternative")
        
        # Try ports in the provided range
        if port_range:
            for port in port_range:
                if (port != preferred_port and 
                    port not in self.reserved_ports and 
                    port not in self.allocated_ports):
                    if self.is_port_available(port):
                        self.logger.info(f"Found available port {port}")
                        self.allocated_ports.add(port)
                        return port
        
        # Fallback: try a dynamic range around the preferred port
        search_range = list(range(preferred_port + 1, preferred_port + 100)) + \
                      list(range(preferred_port - 100, preferred_port))
        
        for port in search_range:
            if (port > 1024 and 
                port not in self.reserved_ports and 
                port not in self.allocated_ports):  # Avoid system ports and allocated ports
                if self.is_port_available(port):
                    self.logger.info(f"Found available port {port} in dynamic range")
                    self.allocated_ports.add(port)
                    return port
        
        raise RuntimeError(f"No available ports found near {preferred_port}")
    
    def allocate_port_pair(self, preferred_http: int = 8080, preferred_ws: int = 8081) -> Tuple[int, int]:
        """
        Allocate a pair of ports for HTTP and WebSocket servers
        
        Args:
            preferred_http: Preferred HTTP server port
            preferred_ws: Preferred WebSocket server port
            
        Returns:
            Tuple of (http_port, websocket_port)
        """
        # Find HTTP port
        http_port = self.find_available_port(preferred_http, self.default_http_ports)
        
        # Find WebSocket port, ensuring it's different from HTTP port
        ws_candidates = [p for p in self.default_ws_ports if p != http_port]
        
        # If preferred WS port is the same as allocated HTTP port, try the next one
        if preferred_ws == http_port:
            preferred_ws = preferred_ws + 1
        
        ws_port = self.find_available_port(preferred_ws, ws_candidates)
        
        self.logger.info(f"Allocated port pair: HTTP={http_port}, WebSocket={ws_port}")
        return http_port, ws_port
    
    def release_port(self, port: int):
        """Release a previously allocated port"""
        if port in self.allocated_ports:
            self.allocated_ports.remove(port)
            self.logger.debug(f"Released port {port}")
    
    def release_port_pair(self, http_port: int, ws_port: int):
        """Release a pair of allocated ports"""
        self.release_port(http_port)
        self.release_port(ws_port)
        self.logger.info(f"Released port pair: HTTP={http_port}, WebSocket={ws_port}")
    
    def wait_for_port_release(self, port: int, timeout: float = 30.0, check_interval: float = 1.0) -> bool:
        """
        Wait for a port to become available
        
        Args:
            port: Port to wait for
            timeout: Maximum time to wait in seconds
            check_interval: How often to check in seconds
            
        Returns:
            True if port becomes available, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_port_available(port):
                self.logger.info(f"Port {port} became available after {time.time() - start_time:.1f}s")
                return True
            
            self.logger.debug(f"Port {port} still in use, waiting...")
            time.sleep(check_interval)
        
        self.logger.warning(f"Timeout waiting for port {port} to become available")
        return False
    
    async def cleanup_port(self, port: int, force: bool = False) -> bool:
        """
        Attempt to cleanup processes using a specific port
        
        Args:
            port: Port to cleanup
            force: Whether to force kill processes
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            import subprocess
            
            # Find processes using the port
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                self.logger.info(f"Found {len(pids)} processes using port {port}: {pids}")
                
                for pid in pids:
                    try:
                        if force:
                            subprocess.run(["kill", "-9", pid], check=True)
                            self.logger.info(f"Force killed process {pid}")
                        else:
                            subprocess.run(["kill", "-15", pid], check=True)
                            self.logger.info(f"Sent SIGTERM to process {pid}")
                    except subprocess.CalledProcessError as e:
                        self.logger.warning(f"Failed to kill process {pid}: {e}")
                
                # Wait a moment for cleanup
                await asyncio.sleep(2.0)
                
                # Check if port is now available
                return self.is_port_available(port)
            else:
                # No processes found using the port
                return self.is_port_available(port)
                
        except Exception as e:
            self.logger.error(f"Error during port cleanup: {e}")
            return False
    
    def get_port_info(self, port: int) -> Optional[dict]:
        """
        Get information about what's using a specific port
        
        Args:
            port: Port to check
            
        Returns:
            Dictionary with process information or None if port is free
        """
        try:
            import subprocess
            
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header line
                    process_line = lines[1]
                    parts = process_line.split()
                    return {
                        "command": parts[0],
                        "pid": parts[1],
                        "user": parts[2],
                        "port": port,
                        "details": process_line
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting port info: {e}")
            return None
