# Autonomous CRM Lead Intelligence Guide

The **Hermes CRM Lead Intelligence Engine** (`odoo_ai_ce`) transforms raw inbound inquiries into qualified sales leads with algorithmic scoring, customer intent classification, company scale profiling, and instant draft responses.

---

## 🎯 Key Intelligence Capabilities

| Metric | Details |
|---|---|
| **Company & Industry Profiling** | Infers industry sector (e.g. *Logistics*, *SaaS*, *Manufacturing*) and company scale (SMB, Mid-Market, Enterprise) from the prospect's email domain, website, and inquiry text. |
| **1–100 Qualification Score** | Analyzes buying urgency, budget signals, project scope, and company profile to rate lead quality. |
| **Purchase Intent Classification** | Categorizes intent level: <br>• 🔥 **High:** Immediate requirement, budget approved.<br>• ⚡ **Medium:** Actively evaluating vendors.<br>• 🌱 **Low:** Informational gathering / student. |
| **Pain Point Extraction** | Distills complex multi-paragraph customer emails into concise, actionable bullet points. |
| **AI Sales Playbook & Draft Reply** | Drafts a personalized introductory email addressing the prospect's specific pain points with a clear Call-To-Action (CTA). |

---

## 🛠️ Step-by-Step Profiling Workflow

### 1. Open Target Lead
Navigate to **CRM > Leads** and open any lead record.

### 2. Profile with Hermes
Click the **"Profile with Hermes"** button in the header.

```
+-----------------------------------------------------------------------------+
| CRM Lead: ERP Implementation Inquiry - Acme Logistics                       |
| [ Profile with Hermes ] [ Convert to Opportunity ] [ Mark Won ]             |
+-----------------------------------------------------------------------------+
```

### 3. Review Intelligence Cards
The wizard analyzes the inquiry and displays:
- **Organization Profiling:** Inferred Industry and Estimated Company Scale.
- **Qualification Assessment:** Numerical score (e.g. `92/100`) with visual progress bar and Intent badge (`HIGH`).
- **Customer Requirements & Pain Points:** Extracted requirements.
- **AI Sales Playbook & Draft Reply:** Formatted response ready to review or edit.

### 4. Apply Profile & Post to Chatter
Click **"Apply Profile & Post to Chatter"**.
- The lead fields (`ai_qualification_score`, `ai_buying_intent`, `ai_company_industry`) are updated.
- A structured briefing note is posted to the CRM chatter.
- Sales representatives can immediately copy or send the drafted reply.

---

## 📦 Batch Mass-Profiling Workflow

1. Navigate to **CRM > Leads** in list view.
2. Select multiple leads using the checkboxes.
3. Click the **Action** menu at the top and choose **"Profile with Hermes"**.
4. Click **"Enqueue Batch Profiling"**.
5. The tasks are dispatched to the asynchronous job queue (`ai_ce.job`) and processed in parallel.
