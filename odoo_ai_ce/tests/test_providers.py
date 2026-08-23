# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestAiCeProviders(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider_ollama = self.env['ai_ce.provider'].create({
            'name': 'Test Ollama',
            'service': 'ollama',
            'api_base': 'http://localhost:11434/v1',
            'priority': 10,
        })
        self.provider_openai = self.env['ai_ce.provider'].create({
            'name': 'Test OpenAI',
            'service': 'openai',
            'api_key': 'test-secret-key',
            'priority': 20,
        })
        self.provider_ollama.fallback_provider_ids = [(6, 0, [self.provider_openai.id])]

    def test_provider_headers(self):
        headers_ollama = self.provider_ollama._get_headers()
        self.assertEqual(headers_ollama["Content-Type"], "application/json")
        self.assertNotIn("Authorization", headers_ollama)

        headers_openai = self.provider_openai._get_headers()
        self.assertEqual(headers_openai["Authorization"], "Bearer test-secret-key")

    @patch("urllib.request.urlopen")
    def test_provider_chat_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices": [{"message": {"content": "Hello from AI!", "tool_calls": []}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.provider_ollama.chat(messages=[{"role": "user", "content": "Hi"}], model_name="llama3.2")
        self.assertEqual(res["content"], "Hello from AI!")
