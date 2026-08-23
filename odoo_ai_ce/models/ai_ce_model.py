# -*- coding: utf-8 -*-
from odoo import models, fields

class AiCeModel(models.Model):
    _name = "ai_ce.model"
    _description = "AI Model Catalog"
    _order = "provider_id asc, name asc"

    name = fields.Char(string="Model Identifier", required=True, help="e.g. gpt-4o, llama3.3:70b, nomic-embed-text")
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    provider_id = fields.Many2one("ai_ce.provider", string="Provider", required=True, ondelete="cascade")
    model_use = fields.Selection([
        ('chat', 'Chat / Reasoning / Tool Use'),
        ('embedding', 'Vector Embedding'),
        ('multimodal', 'Vision / Multimodal'),
    ], string="Model Use", required=True, default='chat')
    
    context_window = fields.Integer(string="Context Window (Tokens)", default=8192)
    supports_tools = fields.Boolean(string="Supports Tool Calling", default=True)
    is_default = fields.Boolean(string="Default Model for Provider", default=False)
    active = fields.Boolean(string="Active", default=True)

    def _compute_display_name(self):
        for rec in self:
            provider_name = rec.provider_id.name if rec.provider_id else "Unknown"
            rec.display_name = f"{rec.name} ({provider_name})"
