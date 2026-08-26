# Configuration, Security & Zero-Trust Governance

`odoo_ai_ce` provides enterprise-grade governance, access controls, and multi-provider configuration to ensure secure, compliant, and sovereign AI operations in Odoo 19 Community Edition.

---

## 🔐 Zero-Trust Security Principles

1. **Least-Privilege Scoping:** AI agents run with the calling user's security context (`request.uid` / `user_id`). The AI cannot access models or records forbidden to the invoking user.
2. **Resource Allowlist:** External MCP clients and agents can only access models explicitly registered and activated in **MCP Resource Allowlist (`ai_ce.resource`)**.
3. **Human-in-the-Loop (HITL) Consent Gate:** Tools marked with `requires_user_consent=True` generate a pending consent record in `ai_ce.consent` rather than executing directly.
4. **Immutable Audit Trail:** Every AI request, prompt token estimate, execution latency, and caller IP is logged in `ai_ce.log`.

---

## 🌐 AI Provider Configuration

Navigate to **AI Hub > Configuration > AI Providers** to manage inference backends.

### Supported Providers

| Provider | Service Type | Recommended Models | Description |
|---|---|---|---|
| **Ollama (Local / Sovereign)** | `ollama` | `hermes-3:latest`, `llama3.3`, `qwen2.5:14b`, `deepseek-r1:14b` | 100% private, on-premise execution. No data leaves your network. Default endpoint: `http://localhost:11434`. |
| **Hermes Local Daemon** | `hermes_local` | `hermes-3-8b`, `hermes-3-70b` | High-performance loopback sidecar running on `http://127.0.0.1:8765`. |
| **OpenAI** | `openai` | `gpt-4o`, `gpt-4o-mini`, `o3-mini` | OpenAI official API with encrypted API key storage. |
| **Azure OpenAI** | `azure_openai` | `gpt-4o`, `gpt-4-turbo` | Enterprise Azure endpoints with custom deployments and API versions. |
| **Anthropic** | `anthropic` | `claude-3-7-sonnet`, `claude-3-5-haiku` | High-intelligence reasoning models via Anthropic Messages API. |
| **Google Gemini** | `gemini` | `gemini-2.0-flash`, `gemini-1.5-pro` | Multimodal and ultra-fast generation via Google AI Studio. |

---

## 🛠️ Tool Registry & Extensibility (`ai_ce.tool`)

Navigate to **AI Hub > Tools & MCP Gateway > Callable Tools Registry**.

Each registered tool defines:
- **`name`**: Tool technical name (e.g. `search_records`, `website_update_seo`).
- **`implementation`**: `builtin` (native Python handler in `tools/`) or `custom` (custom Python code snippet).
- **`requires_user_consent`**: When `True`, triggers the HITL consent queue.
- **`input_schema`**: JSON Schema validating incoming arguments before execution.

### Sandbox Testing Tool Wizard
To safely test any tool with test parameters:
1. Open any tool in **Callable Tools Registry**.
2. Click **"Test Tool in Sandbox"** in the action bar.
3. Provide sample JSON arguments and click **"Execute Test"**.
4. The test runs inside an isolated PostgreSQL savepoint and rolls back state modifications automatically.

---

## 🛡️ Human-in-the-Loop (HITL) Consent Queue (`ai_ce.consent`)

When an agent triggers a sensitive action, a consent record is created with:
- **Requester:** Agent / Discuss user.
- **Action / Tool:** Targeted tool and proposed JSON arguments.
- **Execution Preview:** Summary of affected records.

### Approving or Rejecting Requests
1. Navigate to **AI Hub > Agentic Operations > Pending Approvals (HITL)**.
2. Review the proposed action and JSON payload.
3. Click **"Approve & Execute"** to commit the operation or **"Reject"** to discard.

---

## 📊 Security & Execution Audit Logs (`ai_ce.log`)

Navigate to **AI Hub > Agentic Operations > Security Audit Logs** for a complete audit trail:
- **Timestamp & User:** Exact execution time and invoking Odoo user.
- **Client Type:** `discuss`, `ask_ai`, `mcp_gateway`, `cron_job`, `wizard`.
- **Model Used & Provider:** Active LLM and temperature settings.
- **Latency & Status:** Execution duration in milliseconds and success/failure status.
