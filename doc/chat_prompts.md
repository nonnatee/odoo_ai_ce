# AI Chat & Prompt Playbook

Welcome to the **Hermes AI Agent Chat & Prompt Playbook**. This guide contains battle-tested prompt templates and examples across every major Odoo ERP operational domain, demonstrating how to query data, trigger autonomous tools, generate marketing content, and automate routine workflows.

---

## 🎯 Quick Navigation

- [Sales & CRM Intelligence](#sales-crm-intelligence)
- [Accounting & Financial Queries](#accounting-financial-queries)
- [Inventory & Product Management](#inventory-product-management)
- [Website & E-Commerce Operations](#website-e-commerce-operations)
- [Marketing & Content Studio](#marketing-content-studio)
- [Fast-Path Slash Commands](#fast-path-slash-commands)
- [Multi-Turn Agent Reasoning](#multi-turn-agent-reasoning)

---

## 📊 Sales & CRM Intelligence

### 1. Lead Qualification & Buying Intent
```markdown
Analyze the buying intent and qualification score for Lead #124 (Deco Addict). What are their primary pain points, and what is the recommended next action?
```
> **What Hermes does:** Invokes `crm_analyze_lead`, retrieves company domain data, evaluates budget/timeline signals, calculates a 1–100 score, and returns an executive summary.

### 2. Follow-Up Email Generation
```markdown
Draft a persuasive follow-up email for Quotation SO042, which was sent to Azure Interior 4 days ago. Highlight our 1-year warranty and free installation service.
```

### 3. Pipeline Performance Overview
```markdown
Show me a summary of all opportunities in the 'Qualified' and 'Proposition' stages closing this month, sorted by expected revenue.
```

---

## 💰 Accounting & Financial Queries

### 1. Overdue Invoices Summary
```markdown
Summarize our top 5 overdue customer invoices. Group them by customer, days overdue, and outstanding amount.
```
> **Sample Response:**
> ```
> 1. INV/2026/0014 - Deco Addict: $4,250.00 (34 days overdue)
> 2. INV/2026/0019 - Azure Interior: $3,100.00 (21 days overdue)
> 3. INV/2026/0022 - Ready Mat: $1,850.00 (15 days overdue)
> Total Overdue: $9,200.00
> ```

### 2. Vendor Bills & Cash Outflow
```markdown
What are our unpaid vendor bills due within the next 14 days?
```

### 3. Financial Health Snapshot
```markdown
Give me an executive snapshot of our monthly invoiced revenue compared to the previous month.
```

---

## 📦 Inventory & Product Management

### 1. Low Stock & Reordering Alerts
```markdown
Which products currently have quantity on hand at or below their minimum reordering rule?
```
> **What Hermes does:** Queries `stock.warehouse.orderpoint` and `product.product` to identify items at risk of stockout.

### 2. Best-Selling Products
```markdown
List our top 5 best-selling products by quantity and revenue over the last 90 days.
```

### 3. Product Catalog Multilingual Enrichment
```markdown
Generate rich multilingual product descriptions for Product #45 (Ergonomic Office Chair) in English, Thai, and German. Emphasize lumbar support and breathable mesh.
```

---

## 🌐 Website & E-Commerce Operations

### 1. Website Page Inspection & SEO Audit
```markdown
Inspect our homepage at '/' and check the meta title, description, and snippet structure.
```
> **What Hermes does:** Executes `website_inspect_page` and outputs page publication state, snippet hierarchy, and metadata completeness.

### 2. Responsive QWeb Snippet Generation
```markdown
Generate a modern responsive FAQ accordion snippet with 4 questions about our delivery timelines, warranty, and return policy.
```
> **What Hermes does:** Invokes `website_generate_snippet` with clean Bootstrap 5 markup ready for live insertion.

### 3. Update Website Meta Tags (HITL Gated)
```markdown
Update the SEO meta description for page '/shop' to: 'Discover premium modern furniture, ergonomic office chairs, and modular workstations with free delivery nationwide.'
```
> **What Hermes does:** Prepares the update, detects the state-mutating tool `website_update_page_seo`, and automatically queues a **Human-in-the-Loop (HITL) Consent Request** before applying changes.

---

## 📢 Marketing & Content Studio

### 1. Flash Sale Announcement (LINE Flex Message)
```markdown
Create a high-conversion LINE Flex Message JSON payload announcing our 24-Hour Weekend Flash Sale on all acoustic office pods.
```

### 2. Mass Mailing Campaign Copy
```markdown
Draft an engaging promotional email for our loyalty customers introducing our new eco-friendly bamboo desk collection. Include a compelling subject line and 2 call-to-action buttons.
```

### 3. Knowledge Base Article
```markdown
Write a customer-facing helpdesk article explaining how customers can track their parcel delivery through our customer portal.
```

---

## ⚡ Fast-Path Slash Commands (0ms / 0-Tokens)

Type these commands directly in **Odoo Discuss** or **Direct Chat with Hermes AI Agent** for instant telemetry without consuming LLM API tokens:

| Command | Action | Output |
|---|---|---|
| `/status` or `/ping` | Health Check | Shows active provider, catalog model count, tool count, and pending approvals. |
| `/tools` | Tool Registry | Lists all registered tools and their safety / HITL consent requirements. |
| `/models` | Model Catalog | Displays all configured AI models and providers. |
| `/consent` | Approvals Queue | Shows all pending Human-in-the-Loop consent requests. |
| `/clear` | Session Reset | Wipes conversation history for the active Discuss channel. |
| `/help` | Reference | Displays the command cheat sheet. |

---

## 🔄 Multi-Turn Agent Reasoning Example

Hermes maintains conversation state across turns. You can refine, drill down, or ask follow-up questions naturally:

```
+──────────────────────────────────────────────────────────────────────────+
| 💬 Multi-Turn Operational Dialogue                                      |
+──────────────────────────────────────────────────────────────────────────+
| User:                                                                    |
| "How many sales orders did we confirm this week?"                        |
|                                                                          |
| 🤖 Hermes AI Agent:                                                      |
| We confirmed 18 sales orders this week totaling $34,250.00.              |
|                                                                          |
| User:                                                                    |
| "Which customer placed the largest order, and what was in it?"           |
|                                                                          |
| 🤖 Hermes AI Agent:                                                      |
| The largest order was SO089 by Deco Addict for $12,400.00.               |
| It contains:                                                             |
| - 8x Acoustic Work Pods ($9,600.00)                                      |
| - 8x Ergonomic Mesh Chairs ($2,800.00)                                   |
|                                                                          |
| User:                                                                    |
| "Check if we have enough stock in WH/Stock to fulfill that order."        |
|                                                                          |
| 🤖 Hermes AI Agent:                                                      |
| Stock check for SO089:                                                   |
| - Acoustic Work Pods: 10 on hand (Sufficient)                            |
| - Ergonomic Mesh Chairs: 6 on hand (⚠️ 2 units short)                    |
| Would you like me to draft a purchase order for the 2 missing chairs?     |
+──────────────────────────────────────────────────────────────────────────+
```

---

## 💡 Best Practices for Best Results

1. **Be Specific:** Include record names, IDs, or timeframes (e.g. *"last 30 days"* or *"Quotation SO042"*).
2. **Specify Tone or Language:** Add instructions like *"in Thai"* or *"in a concise professional tone"*.
3. **Use Slash Commands for System Stats:** Use `/status` or `/tools` to instantly check configuration without spending LLM tokens.
4. **Approve Consent Promptly:** State-mutating operations queue a pending request in **AI Hub > Agentic Operations > Pending Approvals (HITL)**.
