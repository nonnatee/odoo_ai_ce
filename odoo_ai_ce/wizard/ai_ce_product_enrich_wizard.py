# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeProductEnrichWizard(models.TransientModel):
    _name = "ai_ce.product.enrich.wizard"
    _description = "Product Catalog Enrichment & Diff Preview Wizard"

    product_tmpl_id = fields.Many2one("product.template", string="Target Product")
    product_tmpl_ids = fields.Many2many("product.template", string="Batch Products")
    is_batch = fields.Boolean(string="Batch Mode", default=False)

    tone = fields.Selection([
        ('Marketing', 'Persuasive & Marketing-Driven'),
        ('Technical', 'Technical, Detailed & Specification-Focused'),
        ('Luxury', 'Premium & Luxury Tone'),
        ('Casual', 'Friendly, Conversational & Engaging'),
    ], string="Copywriting Tone", default='Marketing', required=True)

    language = fields.Selection([
        ('EN', 'English (Global)'),
        ('TH', 'Thai (ภาษาไทย)'),
        ('JA', 'Japanese (日本語)'),
        ('ZH', 'Chinese (中文)'),
        ('DE', 'German (Deutsch)'),
        ('FR', 'French (Français)'),
    ], string="Target Language", default='EN', required=True)

    apply_seo = fields.Boolean(string="Apply SEO Title & Meta Description", default=True)
    apply_description = fields.Boolean(string="Apply Formatted Sales Description", default=True)
    apply_bullets = fields.Boolean(string="Apply Key Highlights & Bullet Points", default=True)

    current_name = fields.Char(string="Current Product Name", readonly=True)
    current_description = fields.Html(string="Current Description", readonly=True)

    proposed_seo_title = fields.Char(string="Proposed SEO Title")
    proposed_seo_description = fields.Text(string="Proposed Meta Description")
    proposed_keywords = fields.Char(string="Proposed Search Keywords")
    proposed_feature_bullets = fields.Html(string="Proposed Key Highlights & Specs")
    proposed_enriched_description = fields.Html(string="Proposed eCommerce Description")

    preview_generated = fields.Boolean(string="Preview Generated", default=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self._context.get('active_ids', [])
        active_model = self._context.get('active_model', '')

        if active_model == 'product.template' and len(active_ids) > 1:
            res['is_batch'] = True
            res['product_tmpl_ids'] = [(6, 0, active_ids)]
        elif active_ids and active_model == 'product.template':
            product = self.env['product.template'].browse(active_ids[0])
            res['product_tmpl_id'] = product.id
            res['current_name'] = product.name
            res['current_description'] = product.description_sale or product.description or ""
        return res

    def action_generate_preview(self):
        """Generate enrichment draft and populate proposed diff fields."""
        self.ensure_one()
        if not self.product_tmpl_id:
            raise UserError(_("Please select a target product."))

        payload = self.product_tmpl_id._generate_enrichment_payload(tone=self.tone, language=self.language)

        self.write({
            'proposed_seo_title': payload.get('seo_title', ''),
            'proposed_seo_description': payload.get('seo_description', ''),
            'proposed_keywords': payload.get('keywords', ''),
            'proposed_feature_bullets': payload.get('feature_bullets', ''),
            'proposed_enriched_description': payload.get('enriched_description', ''),
            'preview_generated': True,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply_to_product(self):
        """Apply the selected proposed fields directly to product.template."""
        self.ensure_one()
        product = self.product_tmpl_id
        if not product:
            raise UserError(_("No target product selected."))

        vals = {
            'ai_last_enriched': fields.Datetime.now(),
            'ai_enrich_status': 'enriched',
        }

        if self.apply_seo:
            if self.proposed_seo_title:
                vals['ai_seo_title'] = self.proposed_seo_title
            if self.proposed_seo_description:
                vals['ai_seo_description'] = self.proposed_seo_description
            if self.proposed_keywords:
                vals['ai_seo_keywords'] = self.proposed_keywords

        if self.apply_bullets and self.proposed_feature_bullets:
            vals['ai_feature_bullets'] = self.proposed_feature_bullets

        if self.apply_description and self.proposed_enriched_description:
            vals['ai_enriched_description'] = self.proposed_enriched_description
            vals['description_sale'] = self.proposed_enriched_description

        product.write(vals)

        product.message_post(
            body=f"<div class='o_ai_response'><strong>✨ Hermes Catalog Enrichment Applied ({self.language}):</strong><br/>"
                 f"<strong>SEO Title:</strong> {self.proposed_seo_title or '-'}<br/>"
                 f"<strong>Keywords:</strong> {self.proposed_keywords or '-'}<br/>"
                 f"{self.proposed_feature_bullets or ''}</div>",
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Product Enriched"),
                'message': _("Product '%s' catalog fields updated successfully.") % product.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_enqueue_batch(self):
        """Enqueue multiple products into Hermes Background Job Queue."""
        self.ensure_one()
        products = self.product_tmpl_ids
        if not products:
            raise UserError(_("No products selected for batch enrichment."))

        job = self.env['ai_ce.job'].create({
            'name': f"Batch Product Enrichment ({len(products)} items)",
            'job_type': 'product_enrich',
            'res_model': 'product.template',
            'res_ids': json.dumps(products.ids),
            'total_items': len(products),
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
