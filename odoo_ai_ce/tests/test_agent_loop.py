# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase

class TestAiCeAgentLoop(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['ai_ce.provider'].create({
            'name': 'Mock Provider',
            'service': 'ollama',
            'api_base': 'http://localhost:11434/v1',
        })
        self.tool_search = self.env['ai_ce.tool'].search([('name', '=', 'search_records')], limit=1)
        self.agent = self.env['ai_ce.agent'].create({
            'name': 'Test Sales Agent',
            'provider_id': self.provider.id,
            'tool_ids': [(6, 0, [self.tool_search.id])] if self.tool_search else [],
            'max_iterations': 3,
        })

    @patch("urllib.request.urlopen")
    def test_agent_single_turn_answer(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices": [{"message": {"content": "There are 3 customers found.", "tool_calls": []}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.agent.run_agent("How many customers do we have?")
        self.assertIn("3 customers found", res["answer"])
        self.assertEqual(res["iterations"], 1)
