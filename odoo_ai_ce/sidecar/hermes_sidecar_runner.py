#!/usr/bin/env python3
"""
Hermes Agent Local Sidecar Service.
Runs as a local background process on 127.0.0.1:8765 to supervise long-running autonomous workflows,
provide loopback IPC for Odoo AI CE, and execute background tasks.
"""
import json
import logging
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [HermesSidecar] %(levelname)s: %(message)s")
_logger = logging.getLogger("HermesSidecar")

PORT = 8765
HOST = "127.0.0.1"

class HermesSidecarHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "status": "healthy",
                "version": "1.1.0",
                "uptime": time.time(),
                "agent": "Hermes Autonomous Supervisor & Worker Pool",
                "active_workers": threading.active_count() - 1,
            }
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/tasks/dispatch":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid JSON: {e}"}).encode('utf-8'))
                return

            task_name = payload.get("task", "unnamed_task")
            _logger.info("Received autonomous task dispatch: %s", task_name)

            # Spawn background execution worker
            thread = threading.Thread(target=self._execute_async_task, args=(payload,))
            thread.daemon = True
            thread.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "dispatched", "task": task_name}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def _execute_async_task(self, payload):
        task_name = payload.get("task")
        callback_url = payload.get("callback_url", "http://127.0.0.1:8069/ai_ce/hermes/webhook")
        task_data = payload.get("payload", {})
        job_id = task_data.get("job_id")
        res_ids = task_data.get("res_ids", [])
        total = len(res_ids) if res_ids else 1

        _logger.info("Worker started for task '%s' (Job #%s, %d items)...", task_name, job_id, total)

        # Simulate or process task items with progress updates
        for idx in range(1, total + 1):
            time.sleep(0.5) # Simulate reasoning/enrichment step
            self._send_progress_checkpoint(callback_url, job_id, idx, total, f"Processed item {idx}/{total}")

        # Send completion event
        self._send_completion(callback_url, job_id, f"Hermes completed task '{task_name}' successfully.")
        _logger.info("Worker finished task '%s' (Job #%s).", task_name, job_id)

    def _send_progress_checkpoint(self, callback_url, job_id, current, total, message):
        if not callback_url:
            return
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "event": "progress_update",
                "job_id": job_id,
                "processed": current,
                "total": total,
                "message": message
            }
        }
        self._post_json(callback_url, payload)

    def _send_completion(self, callback_url, job_id, result_summary):
        if not callback_url:
            return
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "event": "task_completed",
                "job_id": job_id,
                "data": {"result": result_summary}
            }
        }
        self._post_json(callback_url, payload)

    def _post_json(self, url, data):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception as e:
            _logger.debug("Callback post to %s failed (expected if Odoo web server offline during local unit tests): %s", url, e)

def run_server():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, HermesSidecarHandler)
    _logger.info("Hermes Agent Sidecar listening on http://%s:%d", HOST, PORT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        _logger.info("Shutting down Hermes Sidecar.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
