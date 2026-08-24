# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class HermesConnectorController(http.Controller):

    @http.route('/ai_ce/hermes/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def hermes_webhook(self, **kwargs):
        """
        Receives asynchronous task completion callbacks, progress checkpoints, and intermediate thought events
        from the local Hermes Agent Sidecar.
        """
        payload = request.jsonrequest or {}
        event_type = payload.get('event')
        job_id = payload.get('job_id')
        task_id = payload.get('task_id')
        data = payload.get('data', {})

        _logger.info("Hermes webhook event received: %s (job: %s, task: %s)", event_type, job_id, task_id)

        env = request.env(user=1)

        if event_type == 'progress_update' and job_id:
            job = env['ai_ce.job'].sudo().browse(int(job_id))
            if job.exists():
                processed = payload.get('processed', job.processed_items + 1)
                msg = payload.get('message', '')
                job.sudo().write({
                    'processed_items': processed,
                    'error_log': f"{job.error_log or ''}\n{msg}" if msg else job.error_log
                })

        elif event_type == 'task_completed':
            if job_id:
                job = env['ai_ce.job'].sudo().browse(int(job_id))
                if job.exists():
                    job.sudo().write({
                        'state': 'done',
                        'processed_items': job.total_items,
                    })

            session_id = payload.get('session_id')
            if session_id:
                session = env['ai_ce.session'].sudo().browse(int(session_id))
                if session.exists():
                    session.add_message('assistant', f"🚀 **Hermes Sidecar Task Completed:**\n\n{data.get('result', '')}")

        return {"status": "received"}

    @http.route('/ai_ce/hermes/status', type='json', auth='user', methods=['POST', 'GET'])
    def hermes_status(self):
        """
        Returns real-time status and telemetry of the local Hermes sidecar supervisor.
        """
        env = request.env
        sidecar = env['ai_ce.hermes_sidecar'].search([('active', '=', True)], limit=1)
        if not sidecar:
            return {"configured": False, "is_running": False}

        # Auto-check status if possible
        try:
            sidecar.action_ping_sidecar()
        except Exception:
            pass

        return {
            "configured": True,
            "id": sidecar.id,
            "name": sidecar.name,
            "host": sidecar.host,
            "port": sidecar.port,
            "is_running": sidecar.is_running,
            "process_pid": sidecar.process_pid,
            "memory_mb": sidecar.memory_mb,
            "cpu_percent": sidecar.cpu_percent,
            "active_acp_sessions": sidecar.active_acp_sessions,
            "last_heartbeat": str(sidecar.last_heartbeat) if sidecar.last_heartbeat else None,
            "version": sidecar.version or "19.0.2.0"
        }

    @http.route('/ai_ce/hermes/supervisor/control', type='json', auth='user', methods=['POST'])
    def hermes_supervisor_control(self, action='ping', **kwargs):
        """
        Triggers process lifecycle actions (start, stop, restart, ping) from the frontend dashboard.
        """
        env = request.env
        sidecar = env['ai_ce.hermes_sidecar'].search([('active', '=', True)], limit=1)
        if not sidecar:
            return {"error": "No active Hermes Sidecar configured."}

        try:
            if action == 'start':
                sidecar.action_start_process()
            elif action == 'stop':
                sidecar.action_stop_process()
            elif action == 'restart':
                sidecar.action_restart_process()
            elif action == 'ping':
                sidecar.action_ping_sidecar()
            else:
                return {"error": f"Unknown supervisor action: {action}"}

            return self.hermes_status()
        except Exception as e:
            return {"error": str(e), "is_running": sidecar.is_running}

    @http.route('/ai_ce/hermes/acp/prompt', type='json', auth='user', methods=['POST'])
    def hermes_acp_prompt(self, prompt, session_id=None, **kwargs):
        """
        Sends an agent turn to Hermes via the ACP layer.
        """
        env = request.env
        sidecar = env['ai_ce.hermes_sidecar'].search([('active', '=', True)], limit=1)
        if not sidecar or not sidecar.is_running:
            return {"error": "Hermes Sidecar daemon is not running."}

        try:
            # Create ACP session if not provided
            if not session_id:
                sess_info = sidecar.create_acp_session(metadata={"user_id": env.uid})
                session_id = sess_info.get("session_id")

            # Send prompt and get structured turn results
            resp = sidecar.send_acp_prompt(session_id, prompt, stream=False)
            return {
                "session_id": session_id,
                "state": resp.get("state"),
                "events": resp.get("events", []),
                "final_answer": resp.get("final_answer", ""),
                "thought_chain": [e["data"]["content"] for e in resp.get("events", []) if e.get("event") == "thought"]
            }
        except Exception as e:
            _logger.exception("Hermes ACP prompt failure: %s", e)
            return {"error": str(e)}

    @http.route('/ai_ce/hermes/acp/approve', type='json', auth='user', methods=['POST'])
    def hermes_acp_approve(self, session_id, decision='approved', **kwargs):
        """
        Approves or rejects a pending Human-in-the-Loop action for an ACP session.
        """
        env = request.env
        sidecar = env['ai_ce.hermes_sidecar'].search([('active', '=', True)], limit=1)
        if not sidecar or not sidecar.is_running:
            return {"error": "Hermes Sidecar daemon is not running."}

        try:
            resp = sidecar.approve_acp_action(session_id, decision=decision)
            return resp
        except Exception as e:
            return {"error": str(e)}
