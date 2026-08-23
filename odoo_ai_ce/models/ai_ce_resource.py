# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AiCeResource(models.Model):
    _name = "ai_ce.resource"
    _description = "AI Resource Exposure Allowlist"
    _order = "sequence asc, name asc"

    name = fields.Char(string="Resource Name", required=True)
    model_name = fields.Char(string="Odoo Model Technical Name", required=True, index=True, help="e.g. res.partner, sale.order, product.template")
    uri = fields.Char(string="MCP Resource URI", compute="_compute_uri", store=True)
    description = fields.Text(string="Resource Description", help="Description presented to MCP clients and AI agents")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active (Exposed)", default=True)
    
    model_exists = fields.Boolean(string="Model Installed", compute="_compute_model_status")
    record_count = fields.Integer(string="Total Records", compute="_compute_model_status")

    @api.depends('model_name')
    def _compute_uri(self):
        for rec in self:
            rec.uri = f"odoo://{rec.model_name}" if rec.model_name else ""

    def _compute_model_status(self):
        for rec in self:
            if rec.model_name and rec.model_name in self.env:
                rec.model_exists = True
                try:
                    rec.record_count = self.env[rec.model_name].sudo().search_count([])
                except Exception:
                    rec.record_count = 0
            else:
                rec.model_exists = False
                rec.record_count = 0
