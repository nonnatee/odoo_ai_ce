# Odoo AI Community Edition (`odoo_ai_ce`)

[![Odoo Version](https://img.shields.io/badge/Odoo-19.0%20CE-purple.svg)](https://www.odoo.com/)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-JSON--RPC%202.0-orange.svg)](https://modelcontextprotocol.io/)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Autonomous%20Sidecar-red.svg)](#local-hermes-agent-sidecar)

**Odoo AI Community Edition (`odoo_ai_ce`)** is a standalone, enterprise-grade AI and Autonomous Agent framework engineered specifically for **Odoo 19 Community Edition**. It delivers sovereign local LLM inference, autonomous agent workflows, Model Context Protocol (MCP) streamable-HTTP gateway, product catalog enrichment, omni-channel content generation, CRM lead intelligence, and zero-trust security governance.

---

## 📑 Table of Contents

- [Key Capabilities](#-key-capabilities)
- [System Architecture](#-system-architecture)
- [Feature Highlights](#-feature-highlights)
  - [1. Product Catalog Enrichment](#1-product-catalog-enrichment)
  - [2. Hermes Content Studio](#2-hermes-content-studio)
  - [3. Autonomous CRM Lead Intelligence](#3-autonomous-crm-lead-intelligence)
  - [4. Asynchronous Batch Job Queue](#4-asynchronous-batch-job-queue)
  - [5. Model Context Protocol (MCP) Gateway](#5-model-context-protocol-mcp-gateway)
  - [6. Multi-Provider AI Hub](#6-multi-provider-ai-hub)
  - [7. Zero-Trust Security & HITL Governance](#7-zero-trust-security--hitl-governance)
  - [8. Native OWL 3 In-App UX](#8-native-owl-3-in-app-ux)
- [Installation & Quick Start](#-installation--quick-start)
- [Configuration Guide](#-configuration-guide)
- [Local Hermes Agent Sidecar](#-local-hermes-agent-sidecar)
- [Client Integration (Claude Desktop / Cursor / IDEs)](#-client-integration)
- [Documentation Index](#-documentation-index)
- [Automated Testing](#-automated-testing)
- [License & Contributions](#-license--contributions)

---

## 🚀 Key Capabilities

```
+---------------------------------------------------------------------------------------------------+
|                                  ODOO AI CE FRAMEWORK CAPABILITIES                                |
|                                                                                                   |
|  [⚡ In-App Ask AI]        [📦 Product Catalog Enrich]    [🎨 Hermes Content Studio]              |
|  - Ctrl+K Global Modal     - SEO Titles & Descriptions    - Email Campaigns (mass_mailing)        |
|  - HTML Editor /ai Box     - Key Highlights Bullet Specs  - LINE Bot Flex Messages                |
|  - Active Record Context   - 6-Language Translation       - Knowledge Articles & Markdown         |
|  - Real-Time Streaming     - Interactive Diff Preview     - Social & Promotional Copy             |
|                                                                                                   |
|  [🎯 CRM Lead Profiler]    [⚙️ Asynchronous Job Queue]    [🔌 MCP Gateway & Sidecar]              |
|  - 1-100 Lead Scoring      - Non-Blocking Batch Queue     - JSON-RPC 2.0 Streamable HTTP          |
|  - Buying Intent Detection - Live Progress Percentage     - 127.0.0.1:8765 Loopback IPC           |
|  - AI Sales Playbook       - Webhook Progress Stream      - Resource Allowlist & Scoping          |
+---------------------------------------------------------------------------------------------------+
```

---

## 🏛️ System Architecture

```mermaid
flowchart TB
    subgraph Frontend["OWL 3 Frontend Layer (Odoo 19)"]
        AskAI["Ask AI Modal (Ctrl+K)"]
        Editor["HTML Editor /ai Powerbox"]
        Dashboard["AI Control Center Dashboard"]
        EnrichWiz["Product Enrichment Diff Wizard"]
        StudioWiz["Hermes Content Studio Wizard"]
    end

    subgraph Core["odoo_ai_ce Backend Engine"]
        AgentLoop["Autonomous Agent ReAct Loop (ai_ce.agent)"]
        JobQueue["Async Batch Job Queue (ai_ce.job)"]
        ToolReg["Tools Registry (@ai_ce_tool / ai_ce.tool)"]
        Consent["HITL Consent Queue (ai_ce.consent)"]
        AuditLog["Security Audit Trail (ai_ce.log)"]
        VectorStore["pgvector / Semantic Store (ai_ce.vector.chunk)"]
    end

    subgraph Gateways["Connectivity & Supervisor Layer"]
        MCPGateway["Streamable-HTTP MCP Gateway (/ai_ce/mcp_gateway)"]
        Sidecar["Hermes Agent Local Sidecar (127.0.0.1:8765)"]
    end

    subgraph Providers["Multi-Provider LLM Hub"]
        Ollama["Local Ollama / Sovereign Engine"]
        LMStudio["LM Studio / vLLM"]
        OpenAI["OpenAI (GPT-4o / o3-mini)"]
        Azure["Azure OpenAI Enterprise"]
        Claude["Anthropic Claude 3.5 / 3.7"]
        Gemini["Google Gemini 2.0 Flash / Pro"]
    end

    Frontend --> Core
    Core <--> Gateways
    Core --> Providers
    Gateways --> Core
```

---

## 🌟 Feature Highlights

### 1. Product Catalog Enrichment
- **Side-by-Side Diff Preview:** Compares current product data against AI-generated SEO titles, meta descriptions, search keywords, feature bullet points, and eCommerce product descriptions.
- **Multilingual Generation:** Instant generation and translation in **English**, **Thai**, **Japanese**, **Chinese**, **German**, and **French**.
- **Copywriting Tone Selection:** Select between *Persuasive Marketing*, *Technical & Detailed*, *Luxury & Premium*, or *Casual & Friendly*.
- **Selective Field Application:** Checkbox toggles allow applying specific fields while preserving existing values.
- **Batch Processing:** Mass-enrich hundreds of products simultaneously via background queue with chatter change-log summaries.

### 2. Hermes Content Studio
- **Omni-Channel Adapters:**
  - **Marketing Emails (`mass_mailing`):** Eye-catching subject lines, preheaders, and responsive HTML email templates with CTA buttons.
  - **LINE Bot Broadcasts (`odoo_line_bot`):** Short conversational messages and structured **LINE Flex Message JSON** card payloads.
  - **Knowledge & Blog Articles:** Structured long-form Markdown copy with heading hierarchies, executive summaries, and FAQs.
  - **Social Media:** Multi-platform blurbs formatted with hashtags and emojis.
- **One-Click Target Injection:** Direct insertion into active mailing records, LINE push queues, or product templates.

### 3. Autonomous CRM Lead Intelligence
- **Company & Domain Profiling:** Automatically infers industry sector and organization scale tier (SMB, Mid-Market, Enterprise) from lead email domain and website.
- **Qualification Scoring & Intent:** Computes an algorithmic **1–100 Lead Quality Score** and classifies purchase intent (*High - Immediate Need*, *Medium - Active Evaluation*, *Low - Information Gathering*).
- **AI Sales Playbook:** Auto-drafts personalized introductory responses and extracts customer pain points directly into CRM chatter notes.

### 4. Asynchronous Batch Job Queue (`ai_ce.job`)
- **Non-Blocking Execution:** Runs heavy AI tasks (mass product catalog enrichment, lead profiling, embedding indexing) in background workers without freezing user sessions.
- **Real-Time Progress Tracking:** Live percentage computation (`processed / total`) and checkpoint streaming via loopback webhooks.

### 5. Model Context Protocol (MCP) Gateway
- **JSON-RPC 2.0 Streamable-HTTP:** Full compliance with the official Model Context Protocol specification at `/ai_ce/mcp_gateway`.
- **Dynamic Tool Discovery (`tools/list`):** Exposes all active `@ai_ce_tool` methods with automatically inferred JSON Schemas.
- **Resource Exposure (`resources/list`):** Maps allowable Odoo models to `odoo://<model>` URIs.
- **Bearer Token Authentication:** Cryptographically verified API keys with zero-trust isolation.

### 6. Multi-Provider AI Hub
- **Sovereign Local Inference:** Native support for local **Ollama** (`http://localhost:11434/v1`), **LM Studio**, and **vLLM**.
- **Cloud LLM Connectors:** Seamless integration with **OpenAI**, **Azure OpenAI**, **Anthropic Claude**, and **Google Gemini**.
- **Failover & Priority Routing:** Automatic priority-based cascading fallback if primary LLM service encounters rate limits or downtime.

### 7. Zero-Trust Security & HITL Governance
- **Human-in-the-Loop (HITL) Consent Queue (`ai_ce.consent`):** State-mutating operations (`create`, `update`, `delete`) create pending approval requests requiring user confirmation before execution.
- **Strict Resource Allowlist (`ai_ce.resource`):** Enforces a strict whitelist preventing agents and external MCP clients from reading unauthorized models.
- **Audit Logging (`ai_ce.log`):** Granular tracking of user identities, client origins, latency, input previews, and execution outcomes.

### 8. Native OWL 3 In-App UX
- **Global Ask-AI Modal:** Bound to **`Ctrl+K`**, featuring real-time token streaming and multi-turn tool calling steps.
- **HTML Editor Powerbox:** Inline **/ai** drafting and rewriting inside all rich-text fields.
- **AI Control Center Dashboard:** Real-time monitoring of provider status, model latency, Hermes sidecar health, and security audit logs.

---

## 📦 Installation & Quick Start

### 1. Prerequisites
- Odoo 19.0 Community Edition (or Enterprise)
- Python 3.10+
- (Optional) Local Ollama instance for sovereign offline inference:
  ```bash
  ollama run llama3.2
  ollama pull nomic-embed-text
  ```

### 2. Clone into Addons Path
```bash
cd /path/to/your/odoo/custom_addons
git clone https://github.com/nonnatee/odoo_ai_ce.git
```

### 3. Install the Module in Odoo
Add `odoo_ai_ce` to your Odoo configuration `addons_path` and update the apps list:
```bash
odoo-bin -c odoo.conf -d your_database -i odoo_ai_ce
```

---

## ⚙️ Configuration Guide

1. Navigate to **AI Hub > Configuration > Settings**.
2. **Select Default AI Provider:** Choose *Local Ollama*, *OpenAI*, *Azure OpenAI*, *Anthropic Claude*, or *Google Gemini*.
3. **Configure API Keys:** Enter your provider API credentials (stored securely with password masking).
4. **Test Connection:** Open **AI Hub > Configuration > AI Providers**, open your provider record, and click **"Check Connection"**.
5. **Discover Models:** Click **"Fetch Models"** to automatically import available chat and embedding models.
6. **Sync Tools:** Go to **AI Hub > Tools & MCP Gateway > Callable Tools Registry** and click **"Sync Decorated Tools"**.

---

## 🤖 Local Hermes Agent Sidecar

The Hermes Sidecar runs as a local background daemon on `127.0.0.1:8765` to supervise long-running autonomous workflows, execute parallel batch jobs, and stream progress checkpoints back to Odoo.

### Starting the Sidecar Daemon
```bash
python sidecar/hermes_sidecar_runner.py
```

Output:
```
[2026-08-23 08:00:00] [HermesSidecar] INFO: Hermes Agent Sidecar listening on http://127.0.0.1:8765
```

### Health Check
```bash
curl http://127.0.0.1:8765/health
```

---

## 💻 Client Integration

You can connect external AI clients (Claude Desktop, Cursor IDE, Codex, or custom agents) directly to your Odoo instance via the built-in MCP Gateway.

### Generate MCP API Key
1. Go to **AI Hub > Tools & MCP Gateway > Generate MCP Key**.
2. Select your client platform (e.g. *Claude Desktop* or *Cursor*).
3. Click **"Generate & Save Key"**.

### Claude Desktop Configuration (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "odoo_ai_ce": {
      "url": "http://localhost:8069/ai_ce/mcp_gateway",
      "headers": {
        "Authorization": "Bearer YOUR_GENERATED_MCP_KEY"
      }
    }
  }
}
```

### Cursor IDE Configuration
```json
{
  "name": "Odoo AI CE",
  "type": "sse",
  "url": "http://localhost:8069/ai_ce/mcp_gateway",
  "headers": {
    "Authorization": "Bearer YOUR_GENERATED_MCP_KEY"
  }
}
```

---

## 📚 Documentation Index

| Guide | Description |
|---|---|
| 📖 [**Architecture & Security**](doc/architecture.md) | Deep architectural blueprint, data flow, zero-trust security model, and Hermes IPC protocol. |
| 🛍️ [**Product Catalog Enrichment**](doc/product_enrichment.md) | User & administrator guide for SEO generation, multilingual translation, diff preview, and batch enrichment. |
| 🎨 [**Hermes Content Studio**](doc/content_studio.md) | Guide for omni-channel content generation (Marketing emails, LINE Bot Flex messages, Knowledge base, Social). |
| 🔌 [**MCP Gateway Reference**](doc/mcp_gateway.md) | Complete JSON-RPC 2.0 Streamable-HTTP protocol specification, tool calling schema, and client setup. |
| 🤖 [**Hermes Sidecar Reference**](doc/hermes_sidecar.md) | Setup, architecture, worker pool management, and background job queue integration. |
| 🎯 [**CRM Lead Intelligence**](doc/crm_intelligence.md) | Guide for automated CRM lead scoring (1–100), buying intent detection, and sales playbook generation. |

---

## 🧪 Automated Testing

The module includes a comprehensive test suite covering providers, agent loop, MCP gateway, vector RAG, product enrichment, content studio, job queue, and CRM lead scoring.

Run unit tests via Odoo CLI:
```bash
odoo-bin -c odoo.conf -d your_database -u odoo_ai_ce --test-enable --stop-after-init
```

---

## 📄 License & Contributions

- **License:** LGPL-3 (GNU Lesser General Public License v3.0).
- **Author:** Antigravity / Google DeepMind.
- **Contributions:** Pull requests and issues are welcome!
