# -*- coding: utf-8 -*-
import os
import sys
import json
import logging
import subprocess
import urllib.request
import urllib.error
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Global dictionary to track locally spawned subprocesses in memory
_SIDE_PROCESSES = {}

class AiCeHermesSidecar(models.Model):
    _name = "ai_ce.hermes_sidecar"
    _description = "Local Hermes Agent Sidecar & ACP Supervisor"

    name = fields.Char(string="Sidecar Instance", default="Local Hermes Sidecar", required=True)
    host = fields.Char(string="Loopback Host", default="127.0.0.1", required=True)
    port = fields.Integer(string="Port", default=8765, required=True)
    auth_token = fields.Char(string="Loopback Secret Token", copy=False)
    
    # Process & Runtime Supervision
    python_path = fields.Char(string="Python Interpreter Path", default=lambda self: sys.executable, help="Path to python executable (or venv python)")
    auto_spawn = fields.Boolean(string="Auto-Spawn Local Subprocess", default=True, help="Automatically launch the Python sidecar daemon locally")
    process_pid = fields.Integer(string="Daemon PID", readonly=True)
    memory_mb = fields.Float(string="Memory Usage (MB)", readonly=True)
    cpu_percent = fields.Float(string="CPU (%)", readonly=True)
    active_acp_sessions = fields.Integer(string="Active ACP Sessions", readonly=True)
    
    is_running = fields.Boolean(string="Health Status", default=False, readonly=True)
    state = fields.Selection([
        ('stopped', 'Stopped'),
        ('running', 'Running'),
    ], string="Status", compute="_compute_state", store=True, readonly=True)
    last_heartbeat = fields.Datetime(string="Last Heartbeat", readonly=True)
    version = fields.Char(string="Sidecar Version", readonly=True)
    active = fields.Boolean(string="Active", default=True)

    @api.depends('is_running')
    def _compute_state(self):
        for rec in self:
            rec.state = 'running' if rec.is_running else 'stopped'

    def _get_runner_script_path(self):
        """Resolves absolute path to hermes_sidecar_runner.py."""
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(module_path, "sidecar", "hermes_sidecar_runner.py")

    def action_start_process(self):
        """Starts the local Hermes Sidecar daemon as a background subprocess."""
        self.ensure_one()
        script_path = self._get_runner_script_path()
        if not os.path.exists(script_path):
            raise UserError(_("Sidecar script not found at: %s") % script_path)

        py_bin = self.python_path or sys.executable

        # Check if already running
        if self._is_alive():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Hermes Sidecar Already Running"),
                    'message': _("Daemon is already running on %s:%d (PID: %d)") % (self.host, self.port, self.process_pid),
                    'type': 'warning',
                }
            }

        try:
            # Spawn daemon detached
            if os.name == 'nt':
                # Windows detached process
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                DETACHED_PROCESS = 0x00000008
                proc = subprocess.Popen(
                    [py_bin, script_path],
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    close_fds=True
                )
            else:
                # Linux/macOS detached process
                proc = subprocess.Popen(
                    [py_bin, script_path],
                    start_new_session=True,
                    close_fds=True
                )

            _SIDE_PROCESSES[self.id] = proc
            self.write({'process_pid': proc.pid})
            _logger.info("Spawned Hermes Sidecar subprocess PID %d", proc.pid)

            # Wait briefly and verify health
            self.env.cr.commit()
            import time
            time.sleep(1.0)
            self.action_ping_sidecar()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Hermes Sidecar Started"),
                    'message': _("Hermes Agent Daemon started successfully (PID: %d)") % proc.pid,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.exception("Failed to start Hermes Sidecar: %s", e)
            raise UserError(_("Failed to spawn Hermes Sidecar process: %s") % str(e))

    def action_stop_process(self):
        """Stops the local Hermes Sidecar subprocess."""
        self.ensure_one()
        pid = self.process_pid
        if pid:
            try:
                import signal
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
            except Exception as e:
                _logger.warning("Could not terminate PID %d: %s", pid, e)

        _SIDE_PROCESSES.pop(self.id, None)
        self.write({
            'process_pid': 0,
            'is_running': False,
            'memory_mb': 0.0,
            'cpu_percent': 0.0,
            'active_acp_sessions': 0,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Hermes Sidecar Stopped"),
                'message': _("Hermes Daemon has been stopped."),
                'type': 'info',
            }
        }

    def action_restart_process(self):
        """Restarts the local Hermes Sidecar daemon."""
        self.ensure_one()
        self.action_stop_process()
        import time
        time.sleep(0.5)
        return self.action_start_process()

    def _is_alive(self):
        """Internal helper to check if endpoint is currently responding."""
        url = f"http://{self.host}:{self.port}/health"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def action_ping_sidecar(self):
        """Test health and update process telemetry."""
        self.ensure_one()
        url = f"http://{self.host}:{self.port}/health"
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                telemetry = data.get('telemetry', {})
                self.write({
                    'is_running': True,
                    'last_heartbeat': fields.Datetime.now(),
                    'version': data.get('version', '1.0.0'),
                    'process_pid': telemetry.get('pid', self.process_pid),
                    'memory_mb': telemetry.get('memory_mb', 0.0),
                    'cpu_percent': telemetry.get('cpu_percent', 0.0),
                    'active_acp_sessions': telemetry.get('active_acp_sessions', 0),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Hermes Sidecar Healthy"),
                        'message': _("Connected at %s:%d (PID: %d, RAM: %.1f MB)") % (
                            self.host, self.port, telemetry.get('pid', 0), telemetry.get('memory_mb', 0.0)
                        ),
                        'type': 'success',
                        'sticky': False,
                    }
                }
        except Exception as e:
            self.write({'is_running': False})
            raise UserError(_("Hermes Sidecar unreachable at %s:%d - %s") % (self.host, self.port, str(e)))

    # --- ACP (Agent Communication Protocol) Client APIs ---

    def create_acp_session(self, metadata=None):
        """Create a new stateful ACP agent session."""
        self.ensure_one()
        url = f"http://{self.host}:{self.port}/v1/acp/sessions/create"
        body = json.dumps({"metadata": metadata or {}}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def send_acp_prompt(self, session_id, prompt, stream=False):
        """Send a turn to an ACP session."""
        self.ensure_one()
        url = f"http://{self.host}:{self.port}/v1/acp/sessions/{session_id}/prompt"
        body = json.dumps({"prompt": prompt, "stream": stream}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def approve_acp_action(self, session_id, decision="approved"):
        """Resume paused ACP session after Human-in-the-Loop decision."""
        self.ensure_one()
        url = f"http://{self.host}:{self.port}/v1/acp/sessions/{session_id}/approve"
        body = json.dumps({"decision": decision}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
