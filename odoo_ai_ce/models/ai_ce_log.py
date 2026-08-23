# -*- coding: utf-8 -*-
from odoo import models, fields

class AiCeLog(models.Model):
    _name = "ai_ce.log"
    _description = "AI Execution Security Audit Log"
    _order = "create_date desc, id desc"

    timestamp = fields.Datetime(string="Timestamp", default=fields.Datetime.now, readonly=True, index=True)
    user_id = fields.Many2one("res.users", string="Caller User", readonly=True, index=True)
    client_type = fields.Selection([
        ('web', 'Odoo Web Client (Ask AI)'),
        ('mcp', 'External MCP Client'),
        ('hermes', 'Hermes Agent Sidecar'),
        ('bot', 'External Bot Integration'),
    ], string="Client Origin", readonly=True)
    
    tool_id = fields.Many2one("ai_ce.tool", string="Executed Tool", readonly=True)
    model_used = fields.Char(string="LLM Model / Engine", readonly=True)
    execution_time_ms = fields.Float(string="Latency (ms)", readonly=True)
    input_preview = fields.Text(string="Input Payload Preview", readonly=True)
    
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Execution Error'),
        ('consent_blocked', 'Awaiting User Approval'),
    ], string="Execution Status", readonly=True, index=True)
    
    error_message = fields.Text(string="Error Details", readonly=True)
