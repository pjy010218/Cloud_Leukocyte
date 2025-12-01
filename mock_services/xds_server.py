import http.server
import socketserver
import json
import logging
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xDS-Server")

# Global state to hold the current Envoy configuration
# Initial state: Allow everything (or default deny)
CURRENT_CONFIG = {
    "version_info": "0",
    "resources": []
}

class XDSHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        """
        Handle POST requests.
        Envoy sends POST requests for discovery (LDS/CDS/RDS/EDS).
        Symbiosis Compiler sends POST requests to /update to push new policies.
        """
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/update':
            # Internal API for Symbiosis Compiler to push updates
            try:
                new_config = json.loads(post_data)
                global CURRENT_CONFIG
                CURRENT_CONFIG = new_config
                logger.info(f"Received Policy Update. Version: {CURRENT_CONFIG.get('version_info')}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Updated")
            except Exception as e:
                logger.error(f"Update failed: {e}")
                self.send_response(500)
                self.end_headers()
        
        elif self.path == '/v3/discovery:listeners':
            # Envoy LDS Endpoint (Simplified)
            logger.info("Received LDS Request from Envoy")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Wrap the resources in the standard DiscoveryResponse envelope
            response = {
                "version_info": CURRENT_CONFIG["version_info"],
                "resources": CURRENT_CONFIG["resources"],
                "type_url": "type.googleapis.com/envoy.config.listener.v3.Listener",
                "nonce": str(CURRENT_CONFIG["version_info"]) # Simple nonce
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            # Default/Unknown endpoint
            self.send_response(404)
            self.end_headers()

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_server(port=8002):
    with ReusableTCPServer(("", port), XDSHandler) as httpd:
        logger.info(f"xDS Server serving at port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
