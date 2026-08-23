# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    ai_seo_title = fields.Char(string="AI SEO Title", help="SEO Title tag optimized for search engines (60-70 chars)")
    ai_seo_description = fields.Text(string="AI SEO Meta Description", help="Search engine snippet summary (150-160 chars)")
    ai_seo_keywords = fields.Char(string="AI Keywords", help="High-intent search keywords comma-separated")
    ai_feature_bullets = fields.Html(string="AI Key Highlights & Specs", help="Bullet points highlighting core features, benefits, and specifications")
    ai_enriched_description = fields.Html(string="AI Formatted Description", help="Compelling sales and eCommerce product copy")
    
    ai_last_enriched = fields.Datetime(string="Last Enriched On", readonly=True)
    ai_enrich_status = fields.Selection([
        ('draft', 'Not Enriched'),
        ('in_progress', 'Enriching'),
        ('enriched', 'Enriched'),
    ], string="AI Enrichment Status", default='draft', readonly=True)

    def action_open_enrich_wizard(self):
        """Open the interactive before/after diff preview wizard for this product."""
        self.ensure_one()
        return {
            'name': _("Hermes Product Catalog Enrichment"),
            'type': 'ir.actions.act_window',
            'res_model': 'ai_ce.product.enrich.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_tmpl_id': self.id,
                'default_current_name': self.name,
                'default_current_description': self.description_sale or self.description or "",
            }
        }

    def action_ai_enrich_silent(self, tone='Marketing', language='EN'):
        """Directly enrich product fields and log changes to chatter (used by batch jobs)."""
        for product in self:
            try:
                product.ai_enrich_status = 'in_progress'
                payload = product._generate_enrichment_payload(tone=tone, language=language)
                
                vals = {
                    'ai_last_enriched': fields.Datetime.now(),
                    'ai_enrich_status': 'enriched',
                }
                if payload.get('seo_title'):
                    vals['ai_seo_title'] = payload['seo_title']
                if payload.get('seo_description'):
                    vals['ai_seo_description'] = payload['seo_description']
                if payload.get('keywords'):
                    vals['ai_seo_keywords'] = payload['keywords']
                if payload.get('feature_bullets'):
                    vals['ai_feature_bullets'] = payload['feature_bullets']
                if payload.get('enriched_description'):
                    vals['ai_enriched_description'] = payload['enriched_description']
                    vals['description_sale'] = payload['enriched_description']

                product.write(vals)

                # Post summary to chatter
                product.message_post(
                    body=f"<div class='o_ai_response'><strong>✨ Hermes AI Catalog Enrichment Applied ({language}):</strong><br/>"
                         f"<strong>SEO Title:</strong> {payload.get('seo_title', '-')}<br/>"
                         f"<strong>Keywords:</strong> {payload.get('keywords', '-')}<br/>"
                         f"{payload.get('feature_bullets', '')}</div>",
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
            except Exception as e:
                _logger.exception("Failed silent enrichment on product %s: %s", product.name, e)
                product.ai_enrich_status = 'draft'

    def _generate_enrichment_payload(self, tone='Marketing', language='EN'):
        """Call AI provider to draft SEO, description, and feature bullets based on product data."""
        self.ensure_one()
        provider = self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
        if not provider:
            raise UserError(_("No active AI Provider configured in Settings."))

        category_name = self.categ_id.name if self.categ_id else "General"
        attributes_info = []
        for line in self.attribute_line_ids:
            vals = ", ".join(line.value_ids.mapped('name'))
            attributes_info.append(f"{line.attribute_id.name}: {vals}")

        prompt = f"""
You are an expert eCommerce catalog optimizer and product copywriter.
Analyze the following product and generate high-converting, SEO-optimized catalog metadata in language: {language} with tone: {tone}.

Product Name: {self.name}
Category: {category_name}
Attributes/Specs: {'; '.join(attributes_info) if attributes_info else 'N/A'}
Current Description: {self.description_sale or self.description or 'N/A'}
Sales Price: {self.list_price}

Respond STRICTLY with a valid JSON object matching this schema:
{{
    "seo_title": "Compelling Title (60-70 chars max)",
    "seo_description": "Meta description summary with call-to-action (150-160 chars max)",
    "keywords": "comma, separated, high, intent, keywords",
    "feature_bullets": "<ul><li><strong>Feature 1:</strong> Benefit explanation</li><li><strong>Feature 2:</strong> Benefit explanation</li><li><strong>Feature 3:</strong> Benefit explanation</li></ul>",
    "enriched_description": "<p>Engaging, persuasive marketing overview for customers.</p>"
}}
"""
        messages = [
            {"role": "system", "content": "You are a professional eCommerce catalog enrichment AI. You output ONLY JSON."},
            {"role": "user", "content": prompt}
        ]

        response = provider.chat(messages=messages, temperature=0.3)
        content = response.get('content', '').strip()
        
        # Clean markdown wrappers if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            return json.loads(content.strip())
        except Exception as e:
            _logger.error("Failed to parse JSON enrichment response: %s\nRaw: %s", e, content)
            return {
                "seo_title": f"{self.name} - Premium Quality",
                "seo_description": f"Buy {self.name}. High quality, fast delivery, and best value for {category_name}.",
                "keywords": f"{self.name}, {category_name}",
                "feature_bullets": f"<ul><li><strong>High Quality:</strong> Built for durability.</li><li><strong>Best Value:</strong> Premium {category_name}.</li></ul>",
                "enriched_description": f"<p>Discover {self.name}, designed to deliver exceptional performance and reliability.</p>"
            }
