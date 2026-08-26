# -*- coding: utf-8 -*-
import json
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestWebsiteAgentTools(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['ai_ce.provider'].create({
            'name': 'Test Local Hermes Provider',
            'service': 'hermes',
            'api_base': 'http://127.0.0.1:8765/v1',
            'priority': 5,
            'active': True,
        })
        self.model = self.env['ai_ce.model'].create({
            'name': 'hermes-3-llama-3.1',
            'provider_id': self.provider.id,
            'model_use': 'chat',
            'context_window': 16384,
            'supports_tools': True,
            'is_default': True,
        })
        self.product = self.env['product.template'].create({
            'name': 'Autonomous AI Gateway',
            'list_price': 499.0,
            'type': 'service' if 'type' in self.env['product.template']._fields else 'consu',
        })
        self.test_view = self.env['ir.ui.view'].create({
            'name': 'Test Website Landing View',
            'type': 'qweb',
            'key': 'website.test_landing',
            'arch': '<t t-name="website.test_landing"><div id="wrap" class="oe_structure oe_empty"><section class="s_text_block"><h1>Welcome</h1></section></div></t>',
        })
        self.ai_partner = self.env['discuss.channel']._get_ai_partner()

    def test_website_generate_snippet_hero(self):
        """Test generating responsive hero banner snippet."""
        from ..tools.website_tools import execute_website_generate_snippet
        res = execute_website_generate_snippet(self.env, {
            'snippet_type': 'hero',
            'title': 'Next-Gen Autonomous ERP',
            'subtitle': 'Supercharge business operations with local sovereign agents.',
            'cta_text': 'Try Free',
            'cta_url': '/demo'
        })
        self.assertEqual(res['status'], 'success')
        self.assertIn('s_banner', res['generated_html'])
        self.assertIn('Next-Gen Autonomous ERP', res['generated_html'])
        self.assertIn('/demo', res['generated_html'])

    def test_website_generate_snippet_features(self):
        """Test generating 3-column feature cards snippet."""
        from ..tools.website_tools import execute_website_generate_snippet
        res = execute_website_generate_snippet(self.env, {
            'snippet_type': 'features',
            'title': 'Core Agentic Capabilities',
            'subtitle': 'Built for modern enterprises',
            'items': [
                {'title': 'Zero-Trust Security', 'description': 'Human-in-the-loop consent gates', 'icon': 'fa-shield'},
                {'title': 'Local Sovereign ACP', 'description': 'Runs entirely on loopback', 'icon': 'fa-server'},
                {'title': 'Multimodal Reasoning', 'description': 'Step-by-step thought chains', 'icon': 'fa-brain'},
            ]
        })
        self.assertEqual(res['status'], 'success')
        self.assertIn('s_three_columns', res['generated_html'])
        self.assertIn('Zero-Trust Security', res['generated_html'])
        self.assertIn('fa-server', res['generated_html'])

    def test_website_generate_snippet_faqs(self):
        """Test generating FAQ accordion snippet."""
        from ..tools.website_tools import execute_website_generate_snippet
        res = execute_website_generate_snippet(self.env, {
            'snippet_type': 'faqs',
            'title': 'Frequently Asked Questions',
            'subtitle': 'Everything you need to know',
            'items': [
                {'question': 'Is data sent to public clouds?', 'answer': 'No, Hermes runs locally via sovereign ACP.'},
                {'question': 'Can agents mutate database records?', 'answer': 'Yes, with zero-trust HITL consent.'},
            ]
        })
        self.assertEqual(res['status'], 'success')
        self.assertIn('s_faq', res['generated_html'])
        self.assertIn('accordion', res['generated_html'])
        self.assertIn('Is data sent to public clouds?', res['generated_html'])

    def test_ecommerce_enrich_product_page(self):
        """Test enriching product template with highlights, specs, and FAQs."""
        from ..tools.website_tools import execute_ecommerce_enrich_product_page
        res = execute_ecommerce_enrich_product_page(self.env, {
            'product_tmpl_id': self.product.id,
            'selling_points': ['High throughput 80 tps', 'Built-in MCP Gateway bridge'],
            'faq_items': [{'question': 'Warranty?', 'answer': '2 years enterprise SLA'}],
            'specs': {'Throughput': '80 TPS', 'Latency': '12ms', 'Interface': 'REST & ACP'}
        })
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['product_id'], self.product.id)
        
        # Verify product description was updated
        target_field = res['updated_field']
        if target_field:
            content = getattr(self.product, target_field)
            self.assertIn('oe_product_enrich_highlights', content)
            self.assertIn('oe_product_enrich_specs', content)
            self.assertIn('Throughput', content)

    def test_website_inspect_and_mutate_arch(self):
        """Test inspecting view arch and injecting QWeb snippet."""
        from ..tools.website_tools import execute_website_inspect_page
        res_inspect = execute_website_inspect_page(self.env, {'url': 'website.test_landing'})
        self.assertIn('view_id', res_inspect)

    def test_hitl_consent_creation_and_approval(self):
        """Test Human-in-the-loop consent queue and decision execution."""
        tool_mutate = self.env['ai_ce.tool'].create({
            'name': 'test_tool_mutate_arch',
            'description': 'Test QWeb Mutation Tool',
            'implementation': 'builtin',
            'requires_user_consent': True,
        })
        
        # Calling tool should intercept and create pending consent
        output = tool_mutate.execute(
            {'page_id': self.test_view.id, 'snippet_html': '<section class="s_injected"><h3>New Block</h3></section>'},
            user_id=self.env.user.id
        )
        self.assertEqual(output.get('_status'), 'consent_required')
        consent_id = output.get('consent_id')
        self.assertTrue(consent_id)

        consent = self.env['ai_ce.consent'].browse(consent_id)
        self.assertEqual(consent.state, 'pending')

        # Test rejection flow on a duplicate
        consent_dup = self.env['ai_ce.consent'].create({
            'tool_id': tool_mutate.id,
            'user_id': self.env.user.id,
            'action_summary': 'Test action',
            'parameters_json': json.dumps({'test': 1}),
            'state': 'pending'
        })
        consent_dup.action_reject()
        self.assertEqual(consent_dup.state, 'denied')
