"""
Simple standalone web server for the Miktos web interface
"""
import http.server
import socketserver
import threading
import logging
from pathlib import Path


def start_web_server(port=3000, web_dir=None):
    """Start a simple HTTP server for the web interface"""
    if web_dir is None:
        web_dir = str(Path(__file__).parent / "web")
    
    logger = logging.getLogger('MiktosWebServer')
    
    class MiktosHTTPHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=web_dir, **kwargs)
        
        def do_GET(self):
            if self.path == '/':
                self.path = '/index.html'
            return super().do_GET()
        
        def log_message(self, format, *args):
            # Suppress HTTP request logging unless in debug mode
            if logger.level <= logging.DEBUG:
                logger.debug(format % args)
    
    def run_server():
        try:
            with socketserver.TCPServer(("", port), MiktosHTTPHandler) as httpd:
                logger.info(f"Web interface available at http://localhost:{port}")
                httpd.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
    
    # Start server in daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    return server_thread


if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    start_web_server()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
