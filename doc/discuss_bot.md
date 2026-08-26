# Odoo Discuss & Chat AI Integration Guide

`odoo_ai_ce` integrates an autonomous AI Agent directly into **Odoo Discuss (`discuss.channel`)**, allowing team members to converse with the AI in group channels, project rooms, and 1-on-1 direct chats.

---

## 🤖 Overview

- **Virtual Partner Identity:** The AI operates under the dedicated partner identity **`Hermes AI Agent`**.
- **Context-Aware Reasoning:** The bot maintains conversation history across turns using `ai_ce.session`.
- **Zero-Trust Safety:** Whenever the AI suggests a destructive action or website view modification, it queues a Human-in-the-Loop (HITL) approval request and displays an approval badge in the chat.

---

## 💬 How to Interact with Hermes AI in Discuss

### 1. Direct 1-on-1 Chat

You can start chatting with Hermes AI in two easy ways:

- **🚀 One-Click Launch (Recommended):**
  - Navigate to **AI Hub > Control Center** and click the **"💬 Chat in Discuss"** button in the header.
  - Or click **AI Hub > Agentic Operations > 💬 Chat with Hermes (Discuss)** in the main navigation.
  - This automatically provisions your personal chat channel with `Hermes AI Agent` and opens Odoo Discuss focused on the conversation.

- **➕ Manual Selection in Discuss:**
  - Open the **Discuss** app from the Odoo home menu.
  - In the left sidebar, click the **➕** icon next to **Direct Messages**.
  - Type **`Hermes AI Agent`** and press Enter.

```
+───────────────────────────────────────────────────────────+
| Hermes AI Agent                                  💬 Chat  |
+───────────────────────────────────────────────────────────+
| User:                                                     |
| "Summarize our top 5 overdue customer invoices."         |
|                                                           |
| 🤖 Hermes AI Agent:                                       |
| Here are the 5 largest overdue invoices as of today:      |
| 1. INV/2026/0014 - Deco Addict: $4,250.00 (34 days)       |
| 2. INV/2026/0019 - Azure Interior: $3,100.00 (21 days)    |
| ...                                                       |
+───────────────────────────────────────────────────────────+
```

### 2. Group Channels & Project Discussions (@Mentions)
In public or private channels (e.g. `#general`, `#sales-leads`, `#support`), invoke the AI by typing `@Hermes`:

```
@Hermes AI Agent Can you analyze the buying intent for Lead #124 and suggest an outreach email?
```

The AI will parse the mention, retrieve the relevant CRM context using active record tools, and reply in the channel.

### 3. Fast-Path Slash Commands (0ms / 0-Tokens)

Hermes AI includes a fast-path command dispatcher inspired by OdooBot that executes instant operational queries directly in Odoo ORM without consuming LLM API tokens or network latency:

| Command | Response Time | Description |
|---|---|---|
| `/status` or `/ping` | `<1 ms` | View active LLM provider, active model, catalog count, and pending approvals. |
| `/tools` | `<1 ms` | Display all registered callable tools, safety flags, and descriptions. |
| `/models` | `<1 ms` | List all available AI models cataloged in the system. |
| `/consent` | `<1 ms` | Check all pending Human-in-the-Loop approval requests in the queue. |
| `/clear` | `<1 ms` | Reset / wipe active conversation session memory for the channel. |
| `/help` | `<1 ms` | Show full list of available slash commands and usage guide. |

---

## 🛡️ Human-in-the-Loop (HITL) Approval Badges

When the AI prepares a write or update action that requires confirmation (such as updating a live website arch or batch-updating records):

```
+───────────────────────────────────────────────────────────+
| 🤖 Hermes AI Agent:                                       |
| I have generated the responsive FAQ accordion snippet.    |
|                                                           |
| ⚠️ Approval Required:                                     |
| This action requires administrator confirmation.          |
| Pending Consent Request #18 has been queued.             |
+───────────────────────────────────────────────────────────+
```

Approvers can navigate to **AI Hub > Agentic Operations > Pending Approvals (HITL)** to inspect and approve the action.

---

## 📚 Example Prompts Library & Playbook

Looking for practical prompt ideas? Check out our dedicated guide:
👉 [**AI Chat Prompts & Playbook (`chat_prompts.md`)**](chat_prompts.md) — featuring ready-to-use prompt templates for Sales, CRM, Overdue Invoices, Low Stock Alerts, Website QWeb snippets, and Marketing copy.

---

## ⚙️ Technical Lifecycle in Discuss

1. **Message Interception:** Hooked via `discuss.channel._message_post_after_hook`.
2. **Author Check:** Messages authored by `Hermes AI Agent` are ignored to eliminate infinite recursion loops.
3. **Session Binding:** Automatically creates or attaches to an `ai_ce.session` linked to the discuss channel (`name="Discuss Channel #<id>"`).
4. **Agent Dispatch:** Executes `agent.run_agent()` with caller context, user credentials, and registered tools.
5. **Response Posting:** Posts the styled HTML response back to the channel with `author_id=Hermes AI Agent`.
