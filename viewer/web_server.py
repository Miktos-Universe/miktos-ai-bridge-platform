"""
Simple HTTP server for serving the Miktos web interface
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
import mimetypes
import os

try:
    from aiohttp import web, WSMsgType  # type: ignore
except ImportError:
    web = None
    WSMsgType = None


class MiktosWebServer:
    """Simple web server for serving the Miktos web interface"""
    
    def __init__(self, port: int = 8080, web_root: Optional[str] = None):
        self.port = port
        self.web_root = web_root or str(Path(__file__).parent / "web")
        self.app = None
        self.site = None
        self.logger = logging.getLogger('MiktosWebServer')
        
    async def start(self):
        """Start the web server"""
        if web is None:
            self.logger.warning("aiohttp not available, falling back to simple HTTP server")
            return await self._start_simple_server()
        
        self.app = web.Application()
        
        # Add routes
        self.app.router.add_get('/', self.serve_index)
        self.app.router.add_get('/{path:.*}', self.serve_static)
        
        # Start server
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        self.site = web.TCPSite(runner, 'localhost', self.port)
        await self.site.start()
        
        self.logger.info(f"Web server started on http://localhost:{self.port}")
        
    async def stop(self):
        """Stop the web server"""
        if self.site:
            await self.site.stop()
            
    async def serve_index(self, request):
        """Serve the main index.html file"""
        index_path = Path(self.web_root) / "index.html"
        
        if not index_path.exists():
            return web.Response(text="Index file not found", status=404)
            
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return web.Response(text=content, content_type='text/html')
        
    async def serve_static(self, request):
        """Serve static files"""
        path = request.match_info['path']
        file_path = Path(self.web_root) / path
        
        # Security check - prevent directory traversal
        try:
            file_path = file_path.resolve()
            web_root_resolved = Path(self.web_root).resolve()
            if not str(file_path).startswith(str(web_root_resolved)):
                return web.Response(text="Access denied", status=403)
        except Exception:
            return web.Response(text="Invalid path", status=400)
            
        if not file_path.exists() or not file_path.is_file():
            return web.Response(text="File not found", status=404)
            
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if content_type is None:
            content_type = 'application/octet-stream'
            
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return web.Response(body=content, content_type=content_type)
        except Exception as e:
            self.logger.error(f"Error serving file {file_path}: {e}")
            return web.Response(text="Internal server error", status=500)
    
    async def _start_simple_server(self):
        """Fallback simple HTTP server using Python's built-in modules"""
        import http.server
        import socketserver
        import threading
        
        class SimpleHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=self.web_root, **kwargs)
                
        def run_server():
            with socketserver.TCPServer(("", self.port), SimpleHandler) as httpd:
                self.logger.info(f"Simple HTTP server started on http://localhost:{self.port}")
                httpd.serve_forever()
                
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
