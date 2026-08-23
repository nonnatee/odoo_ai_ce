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
                        'end_time': http.request.env['ir.fields.converter'].now() if hasattr(http.request.env, 'now') else None
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
        Returns real-time status of the local Hermes sidecar.
        """
        env = request.env
        sidecar = env['ai_ce.hermes_sidecar'].search([('active', '=', True)], limit=1)
        if not sidecar:
            return {"configured": False, "is_running": False}
        return {
            "configured": True,
            "name": sidecar.name,
            "host": sidecar.host,
            "port": sidecar.port,
            "is_running": sidecar.is_running,
            "last_heartbeat": str(sidecar.last_heartbeat) if sidecar.last_heartbeat else None,
            "version": sidecar.version
        }
