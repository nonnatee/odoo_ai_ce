# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeConsent(models.Model):
    _name = "ai_ce.consent"
    _description = "Human-in-the-Loop Approval Queue"
    _order = "create_date desc, id desc"

    session_id = fields.Many2one("ai_ce.session", string="Conversation Session", ondelete="set null")
    tool_id = fields.Many2one("ai_ce.tool", string="Target Tool", required=True)
    user_id = fields.Many2one("res.users", string="Initiating User", required=True, default=lambda self: self.env.user)
    
    action_summary = fields.Text(string="Action Summary", required=True)
    parameters_json = fields.Text(string="Parameters Payload (JSON)")
    
    state = fields.Selection([
        ('pending', 'Pending Approval'),
        ('granted', 'Approved & Executed'),
        ('denied', 'Rejected'),
    ], string="Status", default='pending', required=True, readonly=True)
    
    decided_by_uid = fields.Many2one("res.users", string="Decided By", readonly=True)
    decision_date = fields.Datetime(string="Decision Date", readonly=True)
    execution_result = fields.Text(string="Execution Output", readonly=True)

    def action_approve_and_execute(self):
        """Approve pending request and execute the tool."""
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_("Only pending consent requests can be approved."))
            
            try:
                args = json.loads(rec.parameters_json or "{}")
            except Exception:
                args = {}
                
            # Temporarily bypass consent check since this is the explicit approval
            tool = rec.tool_id
            if tool.implementation == 'builtin':
                from ..tools.builtins import execute_builtin_tool
                res = execute_builtin_tool(self.env, tool.name, args, user_id=rec.user_id.id)
            elif tool.implementation == 'decorator':
                target_model = self.env[tool.decorator_model].with_user(rec.user_id.id)
                method = getattr(target_model, tool.decorator_method)
                res = method(**args)
            else:
                res = {"error": "Unsupported tool implementation."}
                
            rec.write({
                'state': 'granted',
                'decided_by_uid': self.env.user.id,
                'decision_date': fields.Datetime.now(),
                'execution_result': json.dumps(res, indent=2, default=str)
            })
            
            # Post notice to session if available
            if rec.session_id:
                rec.session_id.add_message("assistant", f"✅ Approval granted for `{tool.name}`. Execution completed successfully:\n```json\n{json.dumps(res, indent=2, default=str)}\n```")
                
        return True

    def action_reject(self):
        """Reject pending consent request."""
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_("Only pending consent requests can be rejected."))
            rec.write({
                'state': 'denied',
                'decided_by_uid': self.env.user.id,
                'decision_date': fields.Datetime.now(),
                'execution_result': "Execution rejected by user."
            })
            if rec.session_id:
                rec.session_id.add_message("assistant", f"❌ Action `{rec.tool_id.name}` was rejected by administrator.")
        return True
