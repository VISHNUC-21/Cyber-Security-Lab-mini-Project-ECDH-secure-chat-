#!/usr/bin/env python3
"""Python version of the relay server (standard library only, no pip install).
Serves the web page and forwards messages between the two peers in a room.
It only ever sees PUBLIC keys and CIPHERTEXT."""
import json, os, queue, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("PORT", 3000))
PUB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css"}
rooms = {}                      # room -> {peer_id: queue of outgoing messages}
lock = threading.Lock()


def relay(room, sender, msg):
    with lock:
        for pid, q in rooms.get(room, {}).items():
            if pid != sender:
                q.put(msg)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):          # keep the console clean
        pass

    def params(self):
        u = urlparse(self.path); qs = parse_qs(u.query)
        return u.path, qs.get("room", [""])[0], qs.get("id", [""])[0]

    def do_GET(self):
        path, room, pid = self.params()
        if path == "/events":
            return self.events(room, pid)
        name = "index.html" if path == "/" else path.lstrip("/")
        file = os.path.abspath(os.path.join(PUB, name))
        if not file.startswith(PUB + os.sep) or not os.path.isfile(file):
            return self.send_error(404)
        with open(file, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(os.path.splitext(file)[1], "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def events(self, room, pid):           # peer opens a live stream (SSE)
        q = queue.Queue()
        with lock:
            peers = rooms.setdefault(room, {})
            full = len(peers) >= 2
            if not full:
                peers[pid] = q
        if full:
            return self.send_error(409, "Room full")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        print(f"[{room}] {pid} joined")
        try:
            self.wfile.write(b"retry: 2000\n\n"); self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=2)
                    self.wfile.write(b"data: " + json.dumps(msg).encode() + b"\n\n")
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")   # also detects a closed tab
                self.wfile.flush()
        except OSError:
            pass
        finally:
            with lock:
                peers = rooms.get(room, {})
                peers.pop(pid, None)
                if not peers:
                    rooms.pop(room, None)
            relay(room, pid, {"type": "leave"})
            print(f"[{room}] {pid} left")

    def do_POST(self):                     # peer posts a message
        path, room, pid = self.params()
        if path != "/send":
            return self.send_error(404)
        try:
            msg = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except ValueError:
            return self.send_error(400)
        relay(room, pid, msg)
        print(f"[{room}] server sees from {pid}: {json.dumps(msg)[:120]}")
        self.send_response(204); self.end_headers()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Secure chat running -> http://localhost:{PORT}  (open it in TWO tabs, Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
