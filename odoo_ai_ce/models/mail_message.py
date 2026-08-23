# -*- coding: utf-8 -*-
from odoo import models, fields

class MailMessage(models.Model):
    _inherit = "mail.message"

    ai_role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('tool', 'Tool Output'),
        ('system', 'System Directive'),
    ], string="AI Message Role", index=True)
    
    body_json = fields.Text(string="Structured AI Payload (JSON)")

class MailMail(models.Model):
    _inherit = "mail.mail"

    ai_role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('tool', 'Tool Output'),
        ('system', 'System Directive'),
    ], string="AI Message Role")
    
    body_json = fields.Text(string="Structured AI Payload (JSON)")
