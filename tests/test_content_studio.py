# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase

class TestAiCeContentStudio(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['ai_ce.provider'].create({
            'name': 'Mock Provider Content Studio',
            'service': 'ollama',
            'api_base': 'http://localhost:11434/v1',
            'active': True,
        })
        self.product = self.env['product.template'].create({
            'name': 'Smart Office Desk',
            'list_price': 450.0,
        })

    @patch("urllib.request.urlopen")
    def test_content_studio_generation_and_inject(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'''{
            "choices": [{
                "message": {
                    "content": "{\\"subject\\": \\"Upgrade Your Workspace Today\\", \\"preheader\\": \\"Special Summer Sale\\", \\"body_html\\": \\"<h2>Ergonomic Excellence</h2>\\", \\"line_flex_json\\": \\"{}\\", \\"markdown_content\\": \\"# Smart Desk\\"}"
                }
            }]
        }'''
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        wizard = self.env['ai_ce.content.studio.wizard'].create({
            'channel': 'email',
            'topic': 'Summer Mega Sale',
            'target_audience': 'Remote Workers',
            'campaign_goal': 'Claim 20% discount',
            'tone': 'Persuasive',
            'language': 'EN',
            'res_model': 'product.template',
            'res_id': self.product.id,
        })

        wizard.action_generate_content()

        self.assertTrue(wizard.is_generated)
        self.assertEqual(wizard.generated_subject, "Upgrade Your Workspace Today")
        self.assertIn("Ergonomic Excellence", wizard.generated_body_html)

        # Test injection into target record
        wizard.action_inject_to_target()
        self.assertIn("Ergonomic Excellence", self.product.description_sale)
