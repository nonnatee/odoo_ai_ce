# -*- coding: utf-8 -*-
import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase

class TestAiCeJobQueue(TransactionCase):

    def setUp(self):
        super().setUp()
        self.p1 = self.env['product.template'].create({'name': 'Item 1', 'list_price': 10})
        self.p2 = self.env['product.template'].create({'name': 'Item 2', 'list_price': 20})

    @patch("urllib.request.urlopen")
    def test_batch_job_execution(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"choices": [{"message": {"content": "{\\"seo_title\\": \\"Item\\", \\"seo_description\\": \\"Desc\\", \\"keywords\\": \\"k\\", \\"feature_bullets\\": \\"b\\", \\"enriched_description\\": \\"d\\"}"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        # Create active provider
        self.env['ai_ce.provider'].create({
            'name': 'Test Provider for Job',
            'service': 'ollama',
            'api_base': 'http://localhost:11434/v1',
            'active': True,
        })

        job = self.env['ai_ce.job'].create({
            'name': 'Batch Enrich 2 Products',
            'job_type': 'product_enrich',
            'res_model': 'product.template',
            'res_ids': json.dumps([self.p1.id, self.p2.id]),
            'total_items': 2,
        })

        job.action_run_job()

        self.assertEqual(job.state, 'done')
        self.assertEqual(job.processed_items, 2)
        self.assertEqual(job.progress, 100.0)
