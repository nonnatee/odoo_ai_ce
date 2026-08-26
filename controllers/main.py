# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class AiCeController(http.Controller):

    @http.route('/ai_ce/ask', type='json', auth='user', methods=['POST'])
    def ask_ai(self, prompt, session_id=None, record_context=None, agent_id=None):
        """
        Execute an Ask AI prompt using the assigned or default agent.
        """
        env = request.env
        agent = None
        if agent_id:
            agent = env['ai_ce.agent'].browse(int(agent_id))
        else:
            # Fallback to default active agent
            agent = env['ai_ce.agent'].search([('active', '=', True)], limit=1)
            
        if not agent:
            # Auto-bootstrap default agent if none exist
            provider = env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
            if not provider:
                return {"error": "No AI Provider is configured or active in Settings."}
            agent = env['ai_ce.agent'].create({
                'name': 'Default AI Assistant',
                'provider_id': provider.id,
                'tool_ids': [(6, 0, env['ai_ce.tool'].search([('active', '=', True)]).ids)]
            })

        session = env['ai_ce.session'].browse(int(session_id)) if session_id else None
        
        try:
            result = agent.run_agent(
                user_prompt=prompt,
                session=session,
                record_context=record_context,
                user_id=request.uid
            )
            return result
        except Exception as e:
            _logger.exception("Ask AI execution error")
            return {"error": str(e)}

    @http.route('/ai_ce/log_to_chatter', type='json', auth='user', methods=['POST'])
    def log_to_chatter(self, res_model, res_id, message_body, is_internal_note=True):
        """
        Post an AI-generated answer or summary directly to record chatter.
        """
        env = request.env
        if res_model not in env:
            return {"error": f"Model {res_model} not found."}
            
        record = env[res_model].browse(int(res_id))
        if not record.exists():
            return {"error": "Record not found."}
            
        msg = record.message_post(
            body=f"<div class='o_ai_response'>{message_body}</div>",
            message_type='comment' if not is_internal_note else 'notification',
            subtype_xmlid='mail.mt_note' if is_internal_note else 'mail.mt_comment',
        )
        msg.write({'ai_role': 'assistant'})
        return {"success": True, "message_id": msg.id}

    @http.route('/ai_ce/consent/decide', type='json', auth='user', methods=['POST'])
    def decide_consent(self, consent_id, decision='approved'):
        """
        Handle Human-in-the-Loop decision (approve or reject) for a pending ai_ce.consent request.
        """
        env = request.env
        consent = env['ai_ce.consent'].browse(int(consent_id))
        if not consent.exists():
            return {"error": f"Consent request #{consent_id} not found."}

        if consent.state != 'pending':
            return {"error": f"Consent request #{consent_id} is already in state '{consent.state}'."}

        try:
            if decision in ('approved', 'granted'):
                consent.action_approve_and_execute()
                return {
                    "success": True,
                    "state": consent.state,
                    "decision": "approved",
                    "execution_result": consent.execution_result,
                    "message": f"Consent #{consent_id} approved and executed successfully."
                }
            elif decision in ('rejected', 'denied'):
                consent.action_reject()
                return {
                    "success": True,
                    "state": consent.state,
                    "decision": "rejected",
                    "message": f"Consent #{consent_id} was rejected."
                }
            else:
                return {"error": f"Invalid decision: '{decision}'. Must be 'approved' or 'rejected'."}
        except Exception as e:
            _logger.exception("Error processing consent decision for #%s", consent_id)
            return {"error": str(e)}
