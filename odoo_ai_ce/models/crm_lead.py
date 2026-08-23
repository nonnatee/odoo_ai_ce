# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = "crm.lead"

    ai_company_industry = fields.Char(string="AI Inferred Industry", help="Industry sector identified from company domain/description")
    ai_company_size = fields.Char(string="AI Estimated Company Size", help="Estimated organization scale (e.g. SMB, Mid-Market, Enterprise)")
    ai_qualification_score = fields.Integer(string="AI Lead Score (1-100)", help="Algorithmic qualification score based on buying signals and lead data")
    ai_buying_intent = fields.Selection([
        ('high', '🔥 High - Immediate Need / Budget Ready'),
        ('medium', '⚡ Medium - Active Evaluation'),
        ('low', '🌱 Low - Information Gathering'),
    ], string="AI Purchase Intent", default='medium')
    ai_suggested_response = fields.Text(string="AI Sales Playbook & Draft Reply", help="Personalized introductory response tailored to customer requirements")
    ai_key_pain_points = fields.Text(string="AI Extracted Pain Points & Goals")
    ai_last_profiled = fields.Datetime(string="Last Profiled On", readonly=True)

    def action_open_lead_enrich_wizard(self):
        """Open the CRM Lead Intelligence Profiling Wizard."""
        self.ensure_one()
        return {
            'name': _("Hermes CRM Lead Intelligence"),
            'type': 'ir.actions.act_window',
            'res_model': 'ai_ce.lead.enrich.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            }
        }

    def action_ai_enrich_lead_silent(self):
        """Profile and score lead automatically (used by cron and batch jobs)."""
        for lead in self:
            try:
                intelligence = lead._generate_lead_intelligence()
                lead.write({
                    'ai_company_industry': intelligence.get('industry'),
                    'ai_company_size': intelligence.get('company_size'),
                    'ai_qualification_score': int(intelligence.get('score', 50)),
                    'ai_buying_intent': intelligence.get('intent', 'medium'),
                    'ai_suggested_response': intelligence.get('suggested_reply'),
                    'ai_key_pain_points': intelligence.get('pain_points'),
                    'ai_last_profiled': fields.Datetime.now(),
                })

                # Post briefing note to chatter
                lead.message_post(
                    body=f"<div class='o_ai_response'>"
                         f"<strong>🎯 Hermes Lead Intelligence Briefing:</strong><br/>"
                         f"<strong>Qualification Score:</strong> {intelligence.get('score', 50)}/100 ({intelligence.get('intent', 'medium').upper()} Intent)<br/>"
                         f"<strong>Industry:</strong> {intelligence.get('industry', 'N/A')} | <strong>Scale:</strong> {intelligence.get('company_size', 'N/A')}<br/>"
                         f"<strong>Pain Points:</strong> {intelligence.get('pain_points', 'N/A')}<br/><br/>"
                         f"<strong>Suggested Response:</strong><br/><em>{intelligence.get('suggested_reply', '')}</em>"
                         f"</div>",
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
            except Exception as e:
                _logger.exception("Failed silent profiling on CRM lead %s: %s", lead.name, e)

    def _generate_lead_intelligence(self):
        """Invoke AI provider to analyze lead inquiry, company domain, and generate sales strategy."""
        self.ensure_one()
        provider = self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
        if not provider:
            raise UserError(_("No active AI Provider configured in Settings."))

        partner_name = self.partner_name or (self.partner_id.name if self.partner_id else "Prospective Client")
        email_from = self.email_from or ""
        email_domain = email_from.split('@')[-1] if '@' in email_from else "Unknown"

        prompt = f"""
You are a top-tier B2B Sales Strategist and CRM Lead Analyst.
Analyze the following lead and output actionable sales intelligence:

Lead Title: {self.name}
Customer/Company Name: {partner_name}
Contact Email: {email_from} (Domain: {email_domain})
Phone: {self.phone or 'N/A'}
Inquiry / Notes: {self.description or 'No initial message provided'}
Expected Revenue: {self.expected_revenue}

Respond STRICTLY with a valid JSON object matching this schema:
{{
    "industry": "Inferred Industry (e.g. Manufacturing, SaaS, Retail)",
    "company_size": "Estimated size (e.g. 1-10 SMB, 50-200 Mid-Market, 1000+ Enterprise)",
    "score": 85,
    "intent": "high",
    "pain_points": "Bullet summary of main challenges or requirements",
    "suggested_reply": "Professional, personalized email response addressing their needs with clear CTA"
}}
"""
        messages = [
            {"role": "system", "content": "You are a CRM sales intelligence AI. You output ONLY JSON."},
            {"role": "user", "content": prompt}
        ]

        response = provider.chat(messages=messages, temperature=0.2)
        content = response.get('content', '').strip()

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            return json.loads(content.strip())
        except Exception as e:
            _logger.error("Failed to parse lead intelligence JSON: %s\nRaw: %s", e, content)
            return {
                "industry": "General Business",
                "company_size": "SMB",
                "score": 50,
                "intent": "medium",
                "pain_points": "General product inquiry",
                "suggested_reply": f"Hi {partner_name},\n\nThank you for reaching out regarding {self.name}. I'd love to learn more about your requirements and show you how we can help.\n\nBest regards,"
            }
