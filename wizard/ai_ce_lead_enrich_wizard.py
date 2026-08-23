# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeLeadEnrichWizard(models.TransientModel):
    _name = "ai_ce.lead.enrich.wizard"
    _description = "CRM Lead Intelligence Profiling Wizard"

    lead_id = fields.Many2one("crm.lead", string="Target Lead")
    lead_ids = fields.Many2many("crm.lead", string="Batch Leads")
    is_batch = fields.Boolean(string="Batch Mode", default=False)

    proposed_industry = fields.Char(string="Inferred Industry")
    proposed_company_size = fields.Char(string="Estimated Company Scale")
    proposed_score = fields.Integer(string="Qualification Score (1-100)")
    proposed_intent = fields.Selection([
        ('high', '🔥 High - Immediate Need / Budget Ready'),
        ('medium', '⚡ Medium - Active Evaluation'),
        ('low', '🌱 Low - Information Gathering'),
    ], string="Buying Intent")
    proposed_pain_points = fields.Text(string="Key Pain Points & Requirements")
    proposed_reply = fields.Text(string="Draft Sales Response")

    is_profiled = fields.Boolean(string="Profiled", default=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self._context.get('active_ids', [])
        active_model = self._context.get('active_model', '')

        if active_model == 'crm.lead' and len(active_ids) > 1:
            res['is_batch'] = True
            res['lead_ids'] = [(6, 0, active_ids)]
        elif active_ids and active_model == 'crm.lead':
            res['lead_id'] = active_ids[0]
        return res

    def action_generate_intelligence(self):
        """Invoke AI provider to generate lead profiling and draft response."""
        self.ensure_one()
        if not self.lead_id:
            raise UserError(_("Please select a target lead."))

        intelligence = self.lead_id._generate_lead_intelligence()

        self.write({
            'proposed_industry': intelligence.get('industry', ''),
            'proposed_company_size': intelligence.get('company_size', ''),
            'proposed_score': int(intelligence.get('score', 50)),
            'proposed_intent': intelligence.get('intent', 'medium'),
            'proposed_pain_points': intelligence.get('pain_points', ''),
            'proposed_reply': intelligence.get('suggested_reply', ''),
            'is_profiled': True,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply_to_lead(self):
        """Apply intelligence metadata and post draft reply to chatter."""
        self.ensure_one()
        lead = self.lead_id
        if not lead:
            raise UserError(_("No target lead selected."))

        lead.write({
            'ai_company_industry': self.proposed_industry,
            'ai_company_size': self.proposed_company_size,
            'ai_qualification_score': self.proposed_score,
            'ai_buying_intent': self.proposed_intent,
            'ai_suggested_response': self.proposed_reply,
            'ai_key_pain_points': self.proposed_pain_points,
            'ai_last_profiled': fields.Datetime.now(),
        })

        lead.message_post(
            body=f"<div class='o_ai_response'>"
                 f"<strong>🎯 Hermes Lead Intelligence Profile Applied:</strong><br/>"
                 f"<strong>Score:</strong> {self.proposed_score}/100 | <strong>Intent:</strong> {str(self.proposed_intent).upper()}<br/>"
                 f"<strong>Industry:</strong> {self.proposed_industry or 'N/A'} | <strong>Scale:</strong> {self.proposed_company_size or 'N/A'}<br/>"
                 f"<strong>Pain Points:</strong> {self.proposed_pain_points or 'N/A'}<br/><br/>"
                 f"<strong>Draft Reply:</strong><br/><em>{self.proposed_reply or ''}</em></div>",
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Lead Profiled"),
                'message': _("CRM Lead '%s' scored and profiled successfully.") % lead.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_enqueue_batch(self):
        """Enqueue multiple leads into Hermes Background Job Queue."""
        self.ensure_one()
        leads = self.lead_ids
        if not leads:
            raise UserError(_("No leads selected for batch profiling."))

        job = self.env['ai_ce.job'].create({
            'name': f"Batch CRM Lead Profiling ({len(leads)} items)",
            'job_type': 'lead_enrich',
            'res_model': 'crm.lead',
            'res_ids': json.dumps(leads.ids),
            'total_items': len(leads),
            'state': 'pending'
        })
        job.action_run_job()

        return {
            'name': _("Hermes Background Jobs"),
            'type': 'ir.actions.act_window',
            'res_model': 'ai_ce.job',
            'res_id': job.id,
            'view_mode': 'form',
            'target': 'current',
        }
