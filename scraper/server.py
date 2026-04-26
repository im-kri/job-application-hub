"""
Local server for Job Application Command Center.
Serves index.html and scraped_jobs.json from localhost:8080.
No external dependencies — uses Python stdlib only.

Usage:
  python3 scraper/server.py
Then open: http://localhost:8080
"""

import http.server
import socketserver
import os

PORT = 8080
# Serve from the parent folder (where index.html lives)
SERVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)

    def log_message(self, format, *args):
        # Suppress noisy request logs; only show startup message
        pass

    def end_headers(self):
        # Allow local fetch calls (needed for scraped_jobs.json)
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

print(f"\n  Job Application Command Center")
print(f"  Running at → http://localhost:{PORT}")
print(f"  Serving from: {os.path.abspath(SERVE_DIR)}")
print(f"  Press Ctrl+C to stop\n")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
