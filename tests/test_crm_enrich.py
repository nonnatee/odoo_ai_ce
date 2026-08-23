# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase

class TestAiCeCrmEnrich(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['ai_ce.provider'].create({
            'name': 'Mock Provider for CRM',
            'service': 'ollama',
            'api_base': 'http://localhost:11434/v1',
            'active': True,
        })
        self.lead = self.env['crm.lead'].create({
            'name': 'ERP Implementation Inquiry',
            'partner_name': 'Acme Logistics Corp',
            'email_from': 'contact@acmelogistics.com',
            'description': 'Looking to automate warehouse tracking and integrate with LINE bot for delivery drivers.',
        })

    @patch("urllib.request.urlopen")
    def test_lead_profiling_silent(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'''{
            "choices": [{
                "message": {
                    "content": "{\\"industry\\": \\"Logistics & Supply Chain\\", \\"company_size\\": \\"100-500 Mid-Market\\", \\"score\\": 92, \\"intent\\": \\"high\\", \\"pain_points\\": \\"Warehouse automation and driver LINE notifications\\", \\"suggested_reply\\": \\"Hi Acme team, we have standard modules for this.\\"}"
                }
            }]
        }'''
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        self.lead.action_ai_enrich_lead_silent()

        self.assertEqual(self.lead.ai_company_industry, "Logistics & Supply Chain")
        self.assertEqual(self.lead.ai_company_size, "100-500 Mid-Market")
        self.assertEqual(self.lead.ai_qualification_score, 92)
        self.assertEqual(self.lead.ai_buying_intent, "high")
        self.assertIn("Acme team", self.lead.ai_suggested_response)
