# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase

class TestAiCeProductEnrich(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['ai_ce.provider'].create({
            'name': 'Mock Provider for Product Enrich',
            'service': 'ollama',
            'api_base': 'http://localhost:11434/v1',
            'active': True,
        })
        self.product = self.env['product.template'].create({
            'name': 'Wireless Noise-Canceling Headphones',
            'list_price': 199.99,
            'description_sale': 'Comfortable over-ear headphones with active noise cancellation.',
        })

    @patch("urllib.request.urlopen")
    def test_product_enrich_silent(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'''{
            "choices": [{
                "message": {
                    "content": "{\\"seo_title\\": \\"Best Wireless NC Headphones 2026\\", \\"seo_description\\": \\"Experience crystal clear audio and 30-hour battery life.\\", \\"keywords\\": \\"headphones, noise canceling, wireless\\", \\"feature_bullets\\": \\"<ul><li>30hr Battery</li><li>Active NC</li></ul>\\", \\"enriched_description\\": \\"<p>Premium sound.</p>\\"}"
                }
            }]
        }'''
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        self.product.action_ai_enrich_silent(tone='Marketing', language='EN')

        self.assertEqual(self.product.ai_seo_title, "Best Wireless NC Headphones 2026")
        self.assertEqual(self.product.ai_seo_keywords, "headphones, noise canceling, wireless")
        self.assertEqual(self.product.ai_enrich_status, "enriched")
        self.assertIn("30hr Battery", self.product.ai_feature_bullets)
