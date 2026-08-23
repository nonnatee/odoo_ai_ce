# -*- coding: utf-8 -*-
import json
import logging
import uuid
import time
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# In-memory session tracking for MCP
_MCP_SESSIONS = {}

class McpGatewayController(http.Controller):

    @http.route('/ai_ce/mcp_gateway', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def mcp_gateway(self, **kwargs):
        """
        Streamable-HTTP Model Context Protocol (MCP) Server.
        Follows standard JSON-RPC 2.0 specification.
        """
        # Handle CORS Preflight
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Mcp-Session-Id',
            }
            return Response(status=200, headers=headers)

        auth_header = request.httprequest.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return self._json_rpc_error(None, -32000, "Unauthorized: Bearer token required.", status=401)
            
        token = auth_header.split('Bearer ', 1)[1].strip()
        
        # Authenticate token against system parameter or dedicated API key
        env = request.env(user=1) # Sudo for token verification
        valid_key = env['ir.config_parameter'].sudo().get_param('odoo_ai_ce.mcp_api_key')
        
        # If no key set in params, check if token matches active provider/system config
        if valid_key and token != valid_key:
            return self._json_rpc_error(None, -32000, "Unauthorized: Invalid API Key.", status=401)
            
        # Parse JSON-RPC Payload
        try:
            body_bytes = request.httprequest.data
            payload = json.loads(body_bytes.decode('utf-8'))
        except Exception as e:
            return self._json_rpc_error(None, -32700, f"Parse error: {str(e)}", status=400)

        method = payload.get('method')
        msg_id = payload.get('id')
        params = payload.get('params', {})
        
        # Find or create MCP session
        session_id = request.httprequest.headers.get('Mcp-Session-Id') or str(uuid.uuid4())
        
        if method == 'initialize':
            return self._handle_initialize(msg_id, session_id, params)
        elif method == 'notifications/initialized':
            return self._handle_initialized_notif()
        elif method == 'tools/list':
            return self._handle_tools_list(msg_id, session_id)
        elif method == 'tools/call':
            return self._handle_tools_call(msg_id, session_id, params)
        elif method == 'resources/list':
            return self._handle_resources_list(msg_id)
        elif method == 'resources/templates/list':
            return self._handle_resource_templates(msg_id)
        elif method == 'ping':
            return self._json_rpc_result(msg_id, {}, session_id)
        else:
            return self._json_rpc_error(msg_id, -32601, f"Method not found: {method}")

    def _handle_initialize(self, msg_id, session_id, params):
        result = {
            "protocolVersion": "2024-11-05",
            "sessionId": session_id,
            "capabilities": {
                "tools": {},
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                },
                "logging": {}
            },
            "serverInfo": {
                "name": "odoo_ai_ce_mcp_gateway",
                "version": "19.0.1.0"
            }
        }
        return self._json_rpc_result(msg_id, result, session_id)

    def _handle_initialized_notif(self):
        headers = {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        return Response("{}", status=200, headers=headers)

    def _handle_tools_list(self, msg_id, session_id):
        env = request.env(user=1)
        tools = env['ai_ce.tool'].sudo().search([('active', '=', True)])
        tools_payload = []
        
        for t in tools:
            schema = {}
            if t.input_schema:
                try: schema = json.loads(t.input_schema)
                except: schema = {"type": "object", "properties": {}}
            tools_payload.append({
                "name": t.name.replace(' ', '_'),
                "description": t.description or "",
                "inputSchema": schema
            })
            
        return self._json_rpc_result(msg_id, {"tools": tools_payload}, session_id)

    def _handle_tools_call(self, msg_id, session_id, params):
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        start_time = time.time()
        
        env = request.env(user=1)
        # Match tool by name or sanitized name
        tool = env['ai_ce.tool'].sudo().search([
            '|', ('name', '=', tool_name), ('name', '=', tool_name.replace('_', ' '))
        ], limit=1)
        
        if not tool:
            return self._json_rpc_error(msg_id, -32602, f"Tool not found: {tool_name}")

        try:
            output = tool.execute(arguments)
            elapsed_ms = (time.time() - start_time) * 1000.0
            
            # Log audit trail
            env['ai_ce.log'].sudo().create({
                'client_type': 'mcp',
                'tool_id': tool.id,
                'execution_time_ms': elapsed_ms,
                'input_preview': json.dumps(arguments)[:400],
                'status': 'success',
            })
            
            result = {
                "content": [{
                    "type": "text",
                    "text": json.dumps(output, indent=2, default=str)
                }]
            }
            return self._json_rpc_result(msg_id, result, session_id)
        except Exception as e:
            _logger.exception("MCP Tool Execution Error: %s", tool_name)
            return self._json_rpc_error(msg_id, -32603, f"Tool Execution Failed: {str(e)}")

    def _handle_resources_list(self, msg_id):
        env = request.env(user=1)
        resources = env['ai_ce.resource'].sudo().search([('active', '=', True)])
        res_list = []
        for r in resources:
            res_list.append({
                "uri": r.uri or f"odoo://{r.model_name}",
                "name": r.name,
                "description": r.description or f"Odoo model {r.model_name}",
                "mimeType": "application/json"
            })
        return self._json_rpc_result(msg_id, {"resources": res_list})

    def _handle_resource_templates(self, msg_id):
        return self._json_rpc_result(msg_id, {
            "resourceTemplates": [{
                "uriTemplate": "odoo://{model}",
                "name": "Odoo Model Resource Template",
                "mimeType": "application/json"
            }]
        })

    def _json_rpc_result(self, msg_id, result, session_id=None):
        resp_body = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        }
        if session_id:
            headers['Mcp-Session-Id'] = session_id
        return Response(json.dumps(resp_body), status=200, headers=headers)

    def _json_rpc_error(self, msg_id, code, message, status=200):
        resp_body = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        }
        return Response(json.dumps(resp_body), status=status, headers=headers)
