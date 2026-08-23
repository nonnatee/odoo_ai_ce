# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..tools.sandbox import execute_sandboxed_tool

class AiCeTestToolWizard(models.TransientModel):
    _name = "ai_ce.test.tool.wizard"
    _description = "Sandbox Tool Testing Wizard"

    tool_id = fields.Many2one("ai_ce.tool", string="Target Tool", required=True)
    params_json = fields.Text(string="Input Parameters (JSON)", default='{}')
    commit_changes = fields.Boolean(string="Commit Database Changes (Live)", default=False, help="WARNING: If unchecked, the execution runs in a savepoint and rolls back automatically.")
    
    execution_result = fields.Text(string="Execution Output", readonly=True)
    execution_time_ms = fields.Float(string="Execution Time (ms)", readonly=True)
    status = fields.Char(string="Status", readonly=True)

    def action_execute(self):
        self.ensure_one()
        try:
            args = json.loads(self.params_json or "{}")
        except Exception as e:
            raise UserError(_("Invalid JSON in parameters: %s") % str(e))

        res = execute_sandboxed_tool(self.env, self.tool_id, args, commit=self.commit_changes)
        
        self.write({
            'execution_result': json.dumps(res.get('result'), indent=2, default=str) if res.get('success') else res.get('error'),
            'execution_time_ms': res.get('execution_time_ms', 0.0),
            'status': 'Success (Rollback Safe)' if not self.commit_changes and res.get('success') else ('Success (Committed)' if res.get('success') else 'Failed')
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
