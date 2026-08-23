# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_ai_provider_id = fields.Many2one(
        'ai_ce.provider',
        string="Default AI Provider",
        config_parameter='odoo_ai_ce.default_provider_id'
    )
    default_ai_model_id = fields.Many2one(
        'ai_ce.model',
        string="Default Chat Model",
        config_parameter='odoo_ai_ce.default_model_id'
    )
    strict_allowlist = fields.Boolean(
        string="Enforce Strict Resource Allowlist",
        default=True,
        config_parameter='odoo_ai_ce.strict_allowlist',
        help="When enabled, tools and MCP clients can only read models explicitly registered in AI Resources."
    )
    hermes_sidecar_url = fields.Char(
        string="Hermes Sidecar URL",
        default="http://127.0.0.1:8765",
        config_parameter='odoo_ai_ce.hermes_sidecar_url'
    )
    auto_enrich_products_on_create = fields.Boolean(
        string="Auto-Enrich Products on Creation",
        default=False,
        config_parameter='odoo_ai_ce.auto_enrich_products'
    )
    auto_profile_leads_on_create = fields.Boolean(
        string="Auto-Profile CRM Leads on Creation",
        default=False,
        config_parameter='odoo_ai_ce.auto_profile_leads'
    )
