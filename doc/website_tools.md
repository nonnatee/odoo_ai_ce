# Website & E-Commerce AI Tools Guide

The **Website & E-Commerce AI Suite** in `odoo_ai_ce` gives autonomous agents and human editors powerful tools to inspect, generate, and safely modify live Odoo website pages and e-commerce product showcases.

---

## 🚀 Available Tools

| Tool Technical Name | Human Consent Required | Description |
|---|---|---|
| `website_inspect_page` | ❌ No (Read-only) | Inspects a page's QWeb architecture, SEO metadata (title, description, keywords), and publication status. |
| `website_update_seo` | ❌ No | Updates a website page's SEO title, meta description, and keywords. |
| `website_generate_snippet` | ❌ No | Generates fully responsive Bootstrap 5 / QWeb HTML snippet blocks (Hero, Features, Testimonials, Pricing, FAQ Accordion). |
| `website_mutate_page_arch` | ⚠️ **Yes (HITL Gated)** | Injects or appends an HTML/QWeb snippet block into a live website page view architecture. |
| `ecommerce_enrich_product_page` | ❌ No | Injects a high-converting showcase (highlights, spec table, accordion FAQs) into `product.template.website_description`. |

---

## 🔍 1. Inspect Website Pages (`website_inspect_page`)

Allows the AI agent or user to retrieve structural details and metadata from any published or draft website page.

### Input Parameters
```json
{
  "page_id": 14,
  "url": "/about-us"
}
```
*(Either `page_id` or `url` is accepted)*

### Output Data
- **Page Metadata:** Name, URL key, website ID, published status (`is_published`).
- **SEO Metadata:** Website meta title, meta description, meta keywords.
- **View Architecture:** QWeb view ID, key, and complete XML/HTML arch string.

---

## 🏷️ 2. Update Website SEO Metadata (`website_update_seo`)

Empowers AI agents to optimize search engine ranking without manually editing website settings.

### Input Parameters
```json
{
  "page_id": 14,
  "website_meta_title": "Enterprise Cloud ERP Solutions | Acme Corp",
  "website_meta_description": "Discover scalable cloud ERP, autonomous AI workflows, and supply chain automation designed for high-growth enterprises.",
  "website_meta_keywords": "erp, odoo ai, supply chain, cloud automation"
}
```

### Response
```json
{
  "status": "success",
  "message": "SEO metadata updated for page ID 14 (/about-us)",
  "page_id": 14,
  "url": "/about-us"
}
```

---

## 🎨 3. Responsive QWeb Snippet Generator (`website_generate_snippet`)

Generates clean, semantic Bootstrap 5 / Odoo QWeb snippets ready for instant website rendering.

### Supported Snippet Types

1. **`hero`**: Premium banner with headline, subtitle, Call-to-Action (CTA) button, and accent styling.
2. **`features`**: 3-column structured feature card grid with icons and descriptions.
3. **`testimonials`**: Customer quote cards with avatars, names, and company roles.
4. **`pricing`**: Multi-tier pricing table with feature checklists and highlighted badges.
5. **`faq_accordion`**: Interactive collapsible FAQ accordion.

### Example Request: FAQ Accordion
```json
{
  "snippet_type": "faq_accordion",
  "title": "Frequently Asked Questions",
  "items": [
    {
      "q": "Can I deploy the AI models locally?",
      "a": "Yes! odoo_ai_ce supports 100% local sovereign inference via Ollama and vLLM without any data leaving your server."
    },
    {
      "q": "Are state-mutating actions protected?",
      "a": "Yes! Critical actions require Human-in-the-Loop (HITL) consent approval before execution."
    }
  ]
}
```

---

## 🛡️ 4. Live View Arch Mutation (`website_mutate_page_arch`)

Safely updates or extends a website page's live QWeb arch. Because modifying live website code affects public visitors, this tool is strictly gated by the **Human-in-the-Loop (HITL) Consent Queue**.

### Execution Flow
1. **AI Invocation:** Agent calls `website_mutate_page_arch` with `page_id` and `snippet_html`.
2. **Consent Queued:** Instead of mutating immediately, a pending record is created in `ai_ce.consent`.
3. **Admin Review:** Administrators receive a notification and inspect the HTML diff.
4. **Execution:** Upon approval, the view's QWeb arch is modified and committed.

```
[ AI Agent Turn ]
        │
        ▼
[ Human Consent Gate ] ──(State: Pending)──► [ Admin Approval UI ]
        │                                             │
        ▼ (Upon Approval)                             │
[ Mutate ir.ui.view Arch ] ◄──────────────────────────┘
```

---

## 🛒 5. E-Commerce Product Page Showcase (`ecommerce_enrich_product_page`)

Enhances standard product detail pages with structured e-commerce selling elements.

### Features
- **Key Selling Highlights:** 3–5 bullet points highlighting core value propositions.
- **Technical Specification Table:** Key-value matrix rendered in clean table format.
- **Accordion FAQs:** Interactive customer FAQs embedded in the product description.

### Example Request
```json
{
  "product_tmpl_id": 42,
  "selling_points": [
    "Ultra-low latency inference (<50ms)",
    "Full data privacy with local Ollama runtime",
    "Pre-integrated with Odoo CRM and Discuss"
  ],
  "specs": {
    "Architecture": "ARM64 / x86_64",
    "Supported Models": "Hermes 3, Llama 3.3, Qwen 2.5, DeepSeek R1",
    "License": "LGPL-3"
  },
  "faq_items": [
    {
      "q": "Does this require an external GPU?",
      "a": "Quantized models (4-bit/8-bit) run efficiently on standard CPU servers or Apple Silicon."
    }
  ]
}
```
