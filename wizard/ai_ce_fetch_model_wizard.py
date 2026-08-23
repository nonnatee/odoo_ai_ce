# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.error
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AiCeFetchModelWizard(models.TransientModel):
    _name = "ai_ce.fetch.model.wizard"
    _description = "Provider Model Discovery Wizard"

    provider_id = fields.Many2one("ai_ce.provider", string="Provider", required=True)
    line_ids = fields.One2many("ai_ce.fetch.model.wizard.line", "wizard_id", string="Discovered Models")

    def action_fetch(self):
        self.ensure_one()
        prov = self.provider_id
        base_url = prov._get_effective_base_url()
        headers = prov._get_headers()
        
        endpoint = f"{base_url}/models"
        req = urllib.request.Request(endpoint, headers=headers, method="GET")
        
        lines = []
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models_list = data.get('data', []) or data.get('models', [])
                
                for m in models_list:
                    m_id = m.get('id') or m.get('name')
                    if m_id:
                        # Determine model use
                        m_use = 'embedding' if 'embed' in m_id.lower() else 'chat'
                        lines.append((0, 0, {
                            'name': m_id,
                            'model_use': m_use,
                            'selected': True
                        }))
        except Exception as e:
            raise UserError(_("Failed to fetch models from %s: %s") % (prov.name, str(e)))

        self.line_ids = [(5, 0, 0)] + lines
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        self.ensure_one()
        imported = 0
        for line in self.line_ids.filtered('selected'):
            existing = self.env['ai_ce.model'].search([
                ('provider_id', '=', self.provider_id.id),
                ('name', '=', line.name)
            ], limit=1)
            if not existing:
                self.env['ai_ce.model'].create({
                    'provider_id': self.provider_id.id,
                    'name': line.name,
                    'model_use': line.model_use,
                })
                imported += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Models Imported"),
                'message': _("Successfully imported %d models into catalog.") % imported,
                'type': 'success',
                'sticky': False,
            }
        }

class AiCeFetchModelWizardLine(models.TransientModel):
    _name = "ai_ce.fetch.model.wizard.line"
    _description = "Discovered Model Item"

    wizard_id = fields.Many2one("ai_ce.fetch.model.wizard")
    name = fields.Char(string="Model ID", required=True)
    model_use = fields.Selection([
        ('chat', 'Chat / Reasoning'),
        ('embedding', 'Embedding'),
        ('multimodal', 'Multimodal'),
    ], default='chat')
    selected = fields.Boolean(string="Import", default=True)
