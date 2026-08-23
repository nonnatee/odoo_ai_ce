# -*- coding: utf-8 -*-
import secrets
import json
from odoo import models, fields, api, _

class AiCeGenerateKeyWizard(models.TransientModel):
    _name = "ai_ce.generate.key.wizard"
    _description = "Generate MCP API Key & Client Configuration Wizard"

    platform = fields.Selection([
        ('claude_desktop', 'Claude Desktop'),
        ('cursor', 'Cursor IDE / Codex'),
        ('hermes', 'Hermes Agent'),
        ('custom', 'Custom HTTP Client'),
    ], string="Target Client", required=True, default='claude_desktop')
    
    generated_key = fields.Char(string="Generated Bearer Token", readonly=True)
    config_snippet = fields.Text(string="Client Configuration JSON", readonly=True)

    def action_generate_key(self):
        self.ensure_one()
        token = secrets.token_hex(24)
        
        # Save token to system parameters
        self.env['ir.config_parameter'].sudo().set_param('odoo_ai_ce.mcp_api_key', token)
        
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8069')
        gateway_url = f"{base_url.rstrip('/')}/ai_ce/mcp_gateway"
        
        if self.platform == 'claude_desktop':
            config = {
                "mcpServers": {
                    "odoo_ai_ce": {
                        "url": gateway_url,
                        "headers": {
                            "Authorization": f"Bearer {token}"
                        }
                    }
                }
            }
        elif self.platform == 'cursor':
            config = {
                "name": "Odoo AI CE",
                "type": "sse",
                "url": gateway_url,
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        else:
            config = {
                "endpoint": gateway_url,
                "authorization": f"Bearer {token}"
            }
            
        self.write({
            'generated_key': token,
            'config_snippet': json.dumps(config, indent=2)
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
