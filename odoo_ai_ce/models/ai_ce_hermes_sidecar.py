# -*- coding: utf-8 -*-
import json
import logging
import urllib.request
import urllib.error
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeHermesSidecar(models.Model):
    _name = "ai_ce.hermes_sidecar"
    _description = "Local Hermes Agent Sidecar Manager"

    name = fields.Char(string="Sidecar Instance", default="Local Hermes Sidecar", required=True)
    host = fields.Char(string="Loopback Host", default="127.0.0.1", required=True)
    port = fields.Integer(string="Port", default=8765, required=True)
    auth_token = fields.Char(string="Loopback Secret Token", copy=False)
    
    is_running = fields.Boolean(string="Health Status", default=False, readonly=True)
    last_heartbeat = fields.Datetime(string="Last Heartbeat", readonly=True)
    version = fields.Char(string="Sidecar Version", readonly=True)
    active = fields.Boolean(string="Active", default=True)

    def action_ping_sidecar(self):
        """Test health endpoint on local sidecar process."""
        self.ensure_one()
        url = f"http://{self.host}:{self.port}/health"
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                self.write({
                    'is_running': True,
                    'last_heartbeat': fields.Datetime.now(),
                    'version': data.get('version', '1.0.0')
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Hermes Sidecar Healthy"),
                        'message': _("Connected to Hermes Sidecar at %s:%d (v%s)") % (self.host, self.port, data.get('version', '1.0.0')),
                        'type': 'success',
                        'sticky': False,
                    }
                }
        except Exception as e:
            self.write({'is_running': False})
            raise UserError(_("Hermes Sidecar unreachable at %s:%d - %s") % (self.host, self.port, str(e)))

    def dispatch_agentic_workflow(self, task_name, payload):
        """Dispatch a background multi-step autonomous task to Hermes Sidecar."""
        self.ensure_one()
        url = f"http://{self.host}:{self.port}/tasks/dispatch"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        } if self.auth_token else {"Content-Type": "application/json"}
        
        body = json.dumps({
            "task": task_name,
            "payload": payload,
            "callback_url": f"/ai_ce/hermes/webhook"
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            _logger.exception("Failed to dispatch task to Hermes Sidecar: %s", e)
            raise UserError(_("Hermes Sidecar dispatch error: %s") % str(e))
