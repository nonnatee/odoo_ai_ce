# Model Context Protocol (MCP) Gateway Reference

The **Model Context Protocol (MCP) Gateway** in `odoo_ai_ce` exposes Odoo models, tools, and resources as a standardized **Streamable-HTTP JSON-RPC 2.0 MCP Server** located at `/ai_ce/mcp_gateway`.

External AI assistants (e.g. Anthropic Claude Desktop, Cursor IDE, OpenAI Codex, or autonomous agents) can connect directly to Odoo to query database records, execute workflows, and perform operations within defined security constraints.

---

## 🌐 Endpoint Details

| Attribute | Specification |
|---|---|
| **Endpoint URL** | `http://<your-odoo-host>:8069/ai_ce/mcp_gateway` |
| **Transport** | Streamable-HTTP (POST & OPTIONS with CORS support) |
| **Protocol** | JSON-RPC 2.0 (MCP Protocol Version: `2024-11-05`) |
| **Authentication** | `Authorization: Bearer <mcp_api_key>` |
| **Session Header** | `Mcp-Session-Id: <uuid>` |

---

## 🔑 Authentication & Generating Keys

1. Navigate to **AI Hub > Tools & MCP Gateway > Generate MCP Key**.
2. Select your client platform (*Claude Desktop*, *Cursor*, *Hermes*, or *Custom HTTP Client*).
3. Click **"Generate & Save Key"**.
4. Copy the generated token or JSON configuration snippet directly into your client's settings.

---

## 💻 Client Configuration Examples

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "odoo_ai_ce": {
      "url": "http://localhost:8069/ai_ce/mcp_gateway",
      "headers": {
        "Authorization": "Bearer 8f7b2c9d4e1a3f5a6b7c8d9e0f1a2b3c"
      }
    }
  }
}
```

### Cursor IDE
In Cursor Settings > Features > MCP Servers:
- **Name:** `Odoo AI CE`
- **Type:** `sse`
- **URL:** `http://localhost:8069/ai_ce/mcp_gateway`
- **Headers:** `{"Authorization": "Bearer 8f7b2c9d4e1a3f5a6b7c8d9e0f1a2b3c"}`

---

## 🛠️ Registering Custom Tools with `@ai_ce_tool`

Any Odoo model method can be exposed to the MCP Gateway and autonomous agents using the `@ai_ce_tool` decorator:

```python
# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.addons.odoo_ai_ce.tools.decorator import ai_ce_tool

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    @ai_ce_tool(
        name="summarize_quotation",
        description="Extract order total, line item count, partner name, and delivery status for a given sale order.",
        input_schema={
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "Database ID of the sale order"}
            },
            "required": ["order_id"]
        },
        requires_consent=False
    )
    def action_ai_summarize_quote(self, order_id):
        order = self.browse(order_id)
        if not order.exists():
            return {"error": "Order not found."}
        return {
            "order_name": order.name,
            "partner_name": order.partner_id.name,
            "amount_total": order.amount_total,
            "state": order.state,
            "line_count": len(order.order_line),
        }
```

After adding decorated methods, navigate to **AI Hub > Tools & MCP Gateway > Callable Tools Registry** and click **"Sync Decorated Tools"**.

---

## 📋 JSON-RPC 2.0 Protocol Methods

### 1. `initialize`
Client sends protocol handshake request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {"name": "claude_desktop", "version": "1.0.0"}
  }
}
```
Server responds with capabilities and session identifier:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "sessionId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "capabilities": {
      "tools": {},
      "resources": {"subscribe": false, "listChanged": false},
      "logging": {}
    },
    "serverInfo": {
      "name": "odoo_ai_ce_mcp_gateway",
      "version": "19.0.1.1"
    }
  }
}
```

### 2. `tools/list`
Returns all active tools registered in `ai_ce.tool`.

### 3. `tools/call`
Executes an authorized tool under the security context of the user:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search_records",
    "arguments": {
      "model": "res.partner",
      "domain": [["is_company", "=", true]],
      "limit": 5
    }
  }
}
```

### 4. `resources/list`
Lists allowable resources based on the `ai_ce.resource` allowlist:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "resources": [
      {
        "uri": "odoo://res.partner",
        "name": "Contacts & Customers",
        "mimeType": "application/json"
      },
      {
        "uri": "odoo://product.template",
        "name": "Product Templates",
        "mimeType": "application/json"
      }
    ]
  }
}
```
