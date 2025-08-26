"""
Simple HTTP server for creating Tavus conversations using only the Python
standard library.

This script implements a minimal backend service that listens for POST
requests on ``/create-conversation`` and, upon receiving a request,
forwards a call to the Tavus API to create a new conversation. The key
advantage of this implementation is that it uses only the Python
standard library (via ``http.server`` and ``json``) together with the
``requests`` package (available in this environment) to avoid external
dependencies like Flask. It is suitable for running in constrained
environments where installing new packages is not possible.

Environment variables required:

* ``TAVUS_API_KEY`` – your Tavus API key (see Tavus docs for how to
  generate one【50317044156855†L7-L17】). This key must remain secret and should never
  be exposed to client‑side code.
* ``PERSONA_ID`` – the persona identifier for your "stream demo assistant"
  persona. You can obtain this from your Tavus dashboard.
* ``REPLICA_ID`` – optional; if provided, overrides the replica
  associated with your persona.

Usage:

```sh
export TAVUS_API_KEY=sk_your_key
export PERSONA_ID=p_your_persona
python3 create_tavus_server.py
```

The server will listen on ``0.0.0.0:8000`` by default. You can change
the port by setting the ``PORT`` environment variable. When a client
POSTs to ``/create-conversation``, the server reads any JSON body
included in the request to support optional parameters like
``conversation_name``. It then calls the Tavus API and returns a JSON
response containing the ``conversation_url`` and ``conversation_id``.

Note: This server is intended for demonstration. In production, you
should secure it behind HTTPS and implement authentication or rate
limiting to prevent abuse. Also, never expose your API key directly to
the front end.
"""

import os
import sys
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import requests


API_KEY = os.environ.get("TAVUS_API_KEY")
PERSONA_ID = os.environ.get("PERSONA_ID")
REPLICA_ID = os.environ.get("REPLICA_ID")

if not API_KEY or not PERSONA_ID:
    sys.stderr.write(
        "Error: TAVUS_API_KEY and PERSONA_ID environment variables must be set.\n"
    )
    sys.exit(1)


class TavusRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for creating Tavus conversations."""

    def do_POST(self):
        """Handle POST requests."""
        if self.path != "/create-conversation":
            self.send_error(404, "Not Found")
            return

        # Determine content length and read the request body (if any)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        extra_params = {}
        if body:
            try:
                extra_params = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON in request body")
                return

        # Construct payload for Tavus API
        payload = {
            "persona_id": PERSONA_ID,
        }
        if REPLICA_ID:
            payload["replica_id"] = REPLICA_ID

        # Merge allowed optional fields
        allowed_keys = {
            "conversation_name",
            "conversational_context",
            "callback_url",
            "properties",
            "audio_only",
        }
        for key in allowed_keys:
            if key in extra_params:
                payload[key] = extra_params[key]

        # Make the API call to Tavus
        headers = {
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        }
        try:
            response = requests.post(
                "https://tavusapi.com/v2/conversations",
                headers=headers,
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": "Failed to contact Tavus API", "details": str(exc)}).encode("utf-8")
            )
            return

        if response.status_code != 200:
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": "Tavus API error", "status_code": response.status_code, "details": response.text}).encode("utf-8")
            )
            return

        data = response.json()
        conversation_url = data.get("conversation_url")
        conversation_id = data.get("conversation_id")
        if not conversation_url:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": "Invalid response from Tavus API", "details": data}).encode("utf-8")
            )
            return

        # Respond with conversation details
        self.send_response(200)
        # Allow cross‑origin requests so that Squarespace can call this endpoint directly.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(
            json.dumps({"conversation_url": conversation_url, "conversation_id": conversation_id}).encode("utf-8")
        )

    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests for CORS."""
        # For CORS preflight, always respond with allowed methods and headers
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        # Override to reduce default logging noise
        sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))


def run_server():
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))
    server_address = (host, port)
    httpd = HTTPServer(server_address, TavusRequestHandler)
    print(f"Serving Tavus conversation server on {host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
