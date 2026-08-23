# Odoo AI Community Edition (`odoo_ai_ce`)

**Version:** 19.0.1.1  
**Category:** Productivity/Artificial Intelligence  
**License:** LGPL-3  
**Author:** Antigravity / Google DeepMind  

---

## Overview

`odoo_ai_ce` is the core AI Hub and Autonomous Agent module for Odoo 19 Community Edition. It introduces local sovereign inference (Ollama/vLLM), cloud LLM providers, Model Context Protocol (MCP) Streamable-HTTP server, Product Catalog Enrichment, Hermes Content Studio, CRM Lead Intelligence, and Zero-Trust Security governance.

---

## Technical Dependencies

- **Odoo Standard Modules:**
  - `base`
  - `web`
  - `mail`
  - `html_editor`
  - `product`
  - `crm`
- **External Python Packages:**
  - Standard library only (`urllib.request`, `json`, `hashlib`, `threading`, `secrets`). No external heavy binary wheels required.

---

## Models Index

| Model Technical Name | Description |
|---|---|
| `ai_ce.provider` | LLM Provider Hub (Ollama, OpenAI, Azure, Anthropic, Gemini) with encrypted keys & priority fallbacks. |
| `ai_ce.model` | Model Catalog (Chat, Embedding, Multimodal). |
| `ai_ce.agent` | Autonomous ReAct Agent engine with system prompt and tool bindings. |
| `ai_ce.tool` | Registered callable tools with JSON Schema and HITL consent controls. |
| `ai_ce.resource` | MCP Resource allowlist mapping models to `odoo://<model>` URIs. |
| `ai_ce.session` | Conversation session persistence and message history. |
| `ai_ce.consent` | Human-in-the-Loop approval queue for state-mutating operations. |
| `ai_ce.vector.chunk` | pgvector / Semantic embedding chunk store for knowledge retrieval. |
| `ai_ce.hermes_sidecar` | Local loopback supervisor manager (`127.0.0.1:8765`). |
| `ai_ce.job` | Asynchronous background batch queue with progress tracking. |
| `ai_ce.log` | Security and execution audit log with caller tracking. |
| `product.template` *(Inherited)* | Product enrichment fields (SEO, feature bullets, eCommerce description). |
| `crm.lead` *(Inherited)* | CRM lead profiling, 1–100 score, buying intent, and sales playbook. |
| `mail.message` *(Inherited)* | AI role metadata tagging (`user`, `assistant`, `tool`, `system`). |
| `res.config.settings` *(Inherited)* | Global AI provider, model, and sidecar configuration. |

---

## Wizards Index

| Wizard Technical Name | Description |
|---|---|
| `ai_ce.product.enrich.wizard` | Product catalog enrichment with side-by-side diff preview & batch mode. |
| `ai_ce.content.studio.wizard` | Omni-channel Content Studio for Email, LINE, Knowledge, and Social. |
| `ai_ce.lead.enrich.wizard` | CRM Lead intelligence profiling and draft sales response. |
| `ai_ce.test.tool.wizard` | Sandbox tool testing harness with PostgreSQL savepoint rollback. |
| `ai_ce.fetch.model.wizard` | Automatic model discovery from provider endpoints (`/v1/models`). |
| `ai_ce.generate.key.wizard` | MCP API Key and client configuration JSON generator. |

---

## Documentation

For full documentation, architecture diagrams, and user guides, see:
- [**Documentation Index**](doc/index.md)
- [**Architecture Blueprint**](doc/architecture.md)
- [**Product Enrichment Guide**](doc/product_enrichment.md)
- [**Content Studio Guide**](doc/content_studio.md)
- [**MCP Gateway Reference**](doc/mcp_gateway.md)
- [**Hermes Sidecar Reference**](doc/hermes_sidecar.md)
- [**CRM Intelligence Guide**](doc/crm_intelligence.md)
