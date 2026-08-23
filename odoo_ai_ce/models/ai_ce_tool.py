# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from ..tools.decorator import get_registered_tools
from ..tools.builtins import execute_builtin_tool

_logger = logging.getLogger(__name__)

class AiCeTool(models.Model):
    _name = "ai_ce.tool"
    _description = "AI Callable Tool Definition"
    _order = "name asc"

    name = fields.Char(string="Tool Name", required=True, index=True)
    description = fields.Text(string="Description", required=True, help="Detailed explanation provided to LLM to understand when and how to call this tool")
    implementation = fields.Selection([
        ('builtin', 'Built-in ORM Tool'),
        ('decorator', 'Decorated Python Method (@ai_ce_tool)'),
        ('hermes', 'Hermes Agent Sidecar Action'),
        ('python', 'Dynamic Python Script'),
    ], string="Implementation Type", required=True, default='builtin')
    
    decorator_model = fields.Char(string="Target Model", help="e.g. sale.order")
    decorator_method = fields.Char(string="Method Name", help="e.g. action_ai_summarize_quote")
    
    input_schema = fields.Text(string="Input Schema (JSON)", default='{"type": "object", "properties": {}}')
    requires_user_consent = fields.Boolean(string="Requires HITL Consent", default=False, help="If checked, executing this tool creates a pending approval request instead of executing immediately")
    required_consent_group_id = fields.Many2one("res.groups", string="Approval Group", help="Group permitted to approve pending consent executions")
    
    default_provider_id = fields.Many2one("ai_ce.provider", string="Bound Provider")
    default_model_id = fields.Many2one("ai_ce.model", string="Bound Model")
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def sync_decorated_tools(self):
        """
        Scan all in-memory @ai_ce_tool decorated methods and register/update ai_ce.tool database records.
        """
        decorated_map = get_registered_tools()
        created_count = 0
        updated_count = 0
        
        for tool_name, meta in decorated_map.items():
            existing = self.search([('name', '=', tool_name)], limit=1)
            vals = {
                'name': tool_name,
                'description': meta.get('description') or tool_name,
                'implementation': 'decorator',
                'decorator_method': meta.get('func_name'),
                'input_schema': json.dumps(meta.get('input_schema', {}), indent=2),
                'requires_user_consent': meta.get('requires_consent', False),
            }
            if existing:
                existing.write(vals)
                updated_count += 1
            else:
                self.create(vals)
                created_count += 1
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Tools Synchronized"),
                'message': _("Synchronized %d new and %d updated decorated tools.") % (created_count, updated_count),
                'sticky': False,
            }
        }

    def to_openai_tool_schema(self):
        """Convert record into standard OpenAI Function/Tool Calling schema."""
        self.ensure_one()
        schema_obj = {}
        if self.input_schema:
            try:
                schema_obj = json.loads(self.input_schema)
            except Exception:
                schema_obj = {"type": "object", "properties": {}}
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description or "",
                "parameters": schema_obj
            }
        }

    def execute(self, arguments, user_id=None, session_id=None):
        """
        Execute tool with given argument dict under security context.
        Handles HITL consent interception.
        """
        self.ensure_one()
        caller_uid = user_id or self.env.uid
        
        # Check Human-in-the-loop consent requirement
        if self.requires_user_consent:
            # Check if execution already approved
            consent_record = self.env['ai_ce.consent'].search([
                ('session_id', '=', session_id),
                ('tool_id', '=', self.id),
                ('state', '=', 'granted')
            ], order='id desc', limit=1)
            
            if not consent_record:
                # Create pending consent request
                new_consent = self.env['ai_ce.consent'].create({
                    'session_id': session_id,
                    'tool_id': self.id,
                    'user_id': caller_uid,
                    'action_summary': f"Requesting approval to execute tool '{self.name}'",
                    'parameters_json': json.dumps(arguments, indent=2, default=str),
                    'state': 'pending'
                })
                return {
                    "_status": "consent_required",
                    "consent_id": new_consent.id,
                    "message": _("Tool execution requires user approval. Pending consent request #%d created.") % new_consent.id
                }

        # Dispatch execution by implementation type
        if self.implementation == 'builtin':
            return execute_builtin_tool(self.env, self.name, arguments, user_id=caller_uid)
        elif self.implementation == 'decorator':
            if not self.decorator_model or not self.decorator_method:
                raise UserError(_("Decorated tool %s missing model or method configuration.") % self.name)
            target_model = self.env[self.decorator_model].with_user(caller_uid)
            method = getattr(target_model, self.decorator_method, None)
            if not method:
                raise UserError(_("Method %s not found on model %s") % (self.decorator_method, self.decorator_model))
            return method(**arguments)
        else:
            raise UserError(_("Implementation '%s' is not supported for direct dispatch.") % self.implementation)
