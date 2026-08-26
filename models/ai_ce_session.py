# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AiCeSession(models.Model):
    _name = "ai_ce.session"
    _description = "AI Conversation Session"
    _order = "create_date desc, id desc"

    name = fields.Char(string="Session Title", default="New Conversation")
    agent_id = fields.Many2one("ai_ce.agent", string="Assigned Agent")
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    channel_id = fields.Many2one("discuss.channel", string="Discuss Channel", index=True, ondelete="cascade")
    
    message_ids = fields.One2many("ai_ce.session.message", "session_id", string="Messages")
    message_count = fields.Integer(string="Message Count", compute="_compute_message_count")
    
    active = fields.Boolean(string="Active", default=True)

    def clear_history(self):
        """Clear all messages in this conversation session."""
        self.ensure_one()
        self.message_ids.unlink()

    @api.depends('message_ids')
    def _compute_message_count(self):
        for rec in self:
            rec.message_count = len(rec.message_ids)

    def get_formatted_history(self, limit=20):
        """Return chronological message dicts for LLM context."""
        self.ensure_one()
        msgs = self.message_ids.sorted('id')[-limit:]
        history = []
        for m in msgs:
            msg_dict = {"role": m.role, "content": m.content or ""}
            if m.tool_call_id:
                msg_dict["tool_call_id"] = m.tool_call_id
            history.append(msg_dict)
        return history

    def add_message(self, role, content, tool_call_id=None):
        """Append a message to the session."""
        self.ensure_one()
        return self.env['ai_ce.session.message'].create({
            'session_id': self.id,
            'role': role,
            'content': content,
            'tool_call_id': tool_call_id
        })

class AiCeSessionMessage(models.Model):
    _name = "ai_ce.session.message"
    _description = "AI Conversation Message"
    _order = "id asc"

    session_id = fields.Many2one("ai_ce.session", string="Session", required=True, ondelete="cascade")
    role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('tool', 'Tool Result'),
        ('system', 'System Context'),
    ], string="Role", required=True)
    content = fields.Text(string="Content")
    tool_call_id = fields.Char(string="Tool Call ID")
    create_date = fields.Datetime(string="Timestamp", readonly=True)
