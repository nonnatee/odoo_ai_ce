# Odoo AI Community Edition (`odoo_ai_ce`) Documentation

Welcome to the comprehensive technical and operational documentation for **Odoo AI Community Edition (`odoo_ai_ce`)**.

---

## 📑 Guides & Reference Manuals

1. [**Architecture & Zero-Trust Security (`architecture.md`)**](architecture.md)
   - Detailed component topology and execution flow.
   - Zero-trust security, least-privilege scoping, and HITL consent queue.
   - Hybrid active record & pgvector RAG grounding architecture.

2. [**Product Catalog Enrichment Guide (`product_enrichment.md`)**](product_enrichment.md)
   - Before/after interactive diff preview modal.
   - Multilingual generation (EN, TH, JA, ZH, DE, FR) and copywriting tones.
   - Asynchronous batch product mass-enrichment workflows.

3. [**Hermes Content Studio Guide (`content_studio.md`)**](content_studio.md)
   - Omni-channel content generation for Mass Mailing campaigns (`mass_mailing`).
   - Structured LINE Bot Flex Message JSON payloads (`odoo_line_bot`).
   - Long-form Knowledge Base articles and social media copy.

4. [**Model Context Protocol (MCP) Gateway Reference (`mcp_gateway.md`)**](mcp_gateway.md)
   - Streamable-HTTP JSON-RPC 2.0 protocol specification (`/ai_ce/mcp_gateway`).
   - Tool discovery, dynamic schema extraction, and resource templates (`odoo://<model>`).
   - Integration configurations for Claude Desktop, Cursor IDE, and custom autonomous agents.

5. [**Hermes Agent Sidecar & Job Queue Reference (`hermes_sidecar.md`)**](hermes_sidecar.md)
   - Local loopback daemon setup and supervision on `127.0.0.1:8765`.
   - Asynchronous background job queue (`ai_ce.job`) and worker pool.
   - Real-time SSE and webhook checkpoint progress streaming.

6. [**Autonomous CRM Lead Intelligence Guide (`crm_intelligence.md`)**](crm_intelligence.md)
   - Automatic company domain profiling and industry inference.
   - 1–100 lead qualification scoring and purchase intent detection.
   - Auto-drafted personalized sales playbooks in CRM chatter notes.
