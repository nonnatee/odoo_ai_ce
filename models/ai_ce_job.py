# -*- coding: utf-8 -*-
import json
import logging
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeJob(models.Model):
    _name = "ai_ce.job"
    _description = "Hermes Asynchronous Background Job"
    _order = "create_date desc, id desc"

    name = fields.Char(string="Task Title", required=True)
    job_type = fields.Selection([
        ('product_enrich', 'Product Catalog Enrichment'),
        ('content_gen', 'Omni-Channel Content Studio'),
        ('lead_enrich', 'CRM Lead Profiling & Intelligence'),
        ('batch_rag', 'Batch Vector Embedding & RAG'),
        ('custom', 'Custom Autonomous Task'),
    ], string="Job Type", required=True, default='product_enrich')

    res_model = fields.Char(string="Target Model", help="e.g. product.template, crm.lead, mass_mailing")
    res_ids = fields.Text(string="Target Record IDs (JSON List)", default="[]")

    total_items = fields.Integer(string="Total Items", default=0)
    processed_items = fields.Integer(string="Processed Items", default=0)
    progress = fields.Float(string="Progress (%)", compute="_compute_progress", store=True)

    state = fields.Selection([
        ('pending', 'Queued'),
        ('running', 'In Progress'),
        ('done', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='pending', required=True, index=True)

    user_id = fields.Many2one("res.users", string="Initiated By", default=lambda self: self.env.user)
    sidecar_id = fields.Many2one("ai_ce.hermes_sidecar", string="Assigned Hermes Sidecar")
    start_time = fields.Datetime(string="Started At", readonly=True)
    end_time = fields.Datetime(string="Completed At", readonly=True)
    error_log = fields.Text(string="Error / Execution Log", readonly=True)

    @api.depends('total_items', 'processed_items')
    def _compute_progress(self):
        for rec in self:
            if rec.total_items > 0:
                rec.progress = min(100.0, round((rec.processed_items / float(rec.total_items)) * 100.0, 1))
            elif rec.state == 'done':
                rec.progress = 100.0
            else:
                rec.progress = 0.0

    def action_run_job(self):
        """Dispatch job execution to Hermes Sidecar or execute in background batch worker."""
        for job in self:
            if job.state not in ('pending', 'failed'):
                continue

            job.write({
                'state': 'running',
                'start_time': fields.Datetime.now(),
                'error_log': False
            })

            # Check if sidecar is available
            sidecar = self.env['ai_ce.hermes_sidecar'].search([('active', '=', True), ('is_running', '=', True)], limit=1)
            if sidecar:
                try:
                    payload = {
                        "job_id": job.id,
                        "job_type": job.job_type,
                        "res_model": job.res_model,
                        "res_ids": json.loads(job.res_ids or "[]"),
                    }
                    sidecar.dispatch_agentic_workflow(f"Job #{job.id}: {job.name}", payload)
                    job.sidecar_id = sidecar.id
                    continue
                except Exception as e:
                    _logger.warning("Sidecar dispatch failed for job %d: %s. Falling back to internal worker.", job.id, e)

            # Internal synchronous/batch execution fallback
            job._execute_internally()

        return True

    def _execute_internally(self):
        """Execute job logic using internal model workers."""
        self.ensure_one()
        try:
            ids_list = json.loads(self.res_ids or "[]")
            if not ids_list and self.res_model:
                ids_list = self.env[self.res_model].search([], limit=self.total_items or 50).ids

            total = len(ids_list)
            self.total_items = total

            if self.job_type == 'product_enrich' and self.res_model in ('product.template', 'product.product'):
                for idx, pid in enumerate(ids_list, 1):
                    record = self.env[self.res_model].browse(pid)
                    if record.exists():
                        record.action_ai_enrich_silent()
                    self.processed_items = idx

            elif self.job_type == 'lead_enrich' and self.res_model == 'crm.lead':
                for idx, lid in enumerate(ids_list, 1):
                    lead = self.env['crm.lead'].browse(lid)
                    if lead.exists():
                        lead.action_ai_enrich_lead_silent()
                    self.processed_items = idx

            self.write({
                'state': 'done',
                'end_time': fields.Datetime.now(),
                'processed_items': total
            })
        except Exception as e:
            _logger.exception("Internal job execution error for job %d", self.id)
            self.write({
                'state': 'failed',
                'end_time': fields.Datetime.now(),
                'error_log': str(e)
            })

    def update_progress(self, processed_increment=1, log_message=None):
        """Update job progress incrementally from sidecar or worker callback."""
        for job in self:
            job.processed_items += processed_increment
            if log_message:
                curr_log = job.error_log or ""
                job.error_log = f"{curr_log}\n[{fields.Datetime.now()}] {log_message}"
            if job.processed_items >= job.total_items and job.total_items > 0:
                job.state = 'done'
                job.end_time = fields.Datetime.now()

    def action_cancel_job(self):
        """Cancel queued or running job."""
        self.write({'state': 'cancelled', 'end_time': fields.Datetime.now()})
        return True
