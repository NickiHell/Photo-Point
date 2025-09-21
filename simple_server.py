"""
Simple HTTP server without external dependencies.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


class NotificationHandler(BaseHTTPRequestHandler):
    """HTTP handler for notification service."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/":
            self.send_json_response({"message": "Notification Service", "version": "1.0.0"})
        elif parsed_url.path == "/health":
            self.send_json_response({"status": "healthy", "service": "notification-service"})
        elif parsed_url.path == "/api/v1/users":
            self.send_json_response({"users": []})
        else:
            self.send_error(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/api/v1/users":
            self.send_json_response({"message": "User created", "id": "user_123"})
        elif parsed_url.path == "/api/v1/notifications/send":
            self.send_json_response({"message": "Notification sent", "id": "notif_456"})
        else:
            self.send_error(404, "Not found")
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def run_server(port=8000):
    """Run the HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, NotificationHandler)
    print(f"Starting notification service on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()