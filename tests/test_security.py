# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestAiCeSecurity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.tool_delete = self.env['ai_ce.tool'].search([('name', '=', 'delete_record')], limit=1)
        if not self.tool_delete:
            self.tool_delete = self.env['ai_ce.tool'].create({
                'name': 'delete_record',
                'description': 'Delete record',
                'implementation': 'builtin',
                'requires_user_consent': True,
            })

    def test_consent_blocking_on_delete(self):
        # Executing a tool with requires_user_consent=True must return consent_required and create ai_ce.consent
        res = self.tool_delete.execute({"model": "res.partner", "ids": [1]})
        self.assertEqual(res.get("_status"), "consent_required")
        self.assertIn("consent_id", res)

        consent_record = self.env['ai_ce.consent'].browse(res["consent_id"])
        self.assertEqual(consent_record.state, "pending")
