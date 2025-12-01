import http.server
import socketserver
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InventoryService")

class InventoryHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/v1/inventory/reserve':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                logger.info(f"Received payload: {data}")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "reserved"}).encode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8080):
    # Allow address reuse to avoid "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), InventoryHandler) as httpd:
        logger.info(f"Inventory Service serving at port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
