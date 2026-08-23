# -*- coding: utf-8 -*-
from odoo.tests.common import HttpCase

class TestAiCeMcpGateway(HttpCase):

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param('odoo_ai_ce.mcp_api_key', 'test-mcp-key-12345')

    def test_mcp_initialize_and_tools_list(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-mcp-key-12345'
        }
        
        # Test Initialize
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test_client", "version": "1.0"}
            }
        }
        res = self.url_open('/ai_ce/mcp_gateway', data=json.dumps(init_payload), headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("sessionId", data.get("result", {}))

        # Test Tools List
        tools_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        res = self.url_open('/ai_ce/mcp_gateway', data=json.dumps(tools_payload), headers=headers)
        self.assertEqual(res.status_code, 200)
        tools_data = res.json()
        tool_names = [t["name"] for t in tools_data.get("result", {}).get("tools", [])]
        self.assertIn("search_records", tool_names)

import json
