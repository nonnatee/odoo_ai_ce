# Product Catalog Enrichment Guide

The **Product Catalog Enrichment Engine** in `odoo_ai_ce` empowers eCommerce managers, catalog administrators, and sales teams to automatically generate high-converting product copy, SEO metadata, technical bullet points, and multilingual translations with a single click.

---

## 📋 Features Overview

- **Interactive Diff Preview:** Review proposed changes side-by-side against current values before saving.
- **Selective Field Updates:** Choose exactly which fields to update (SEO title/meta, bullet highlights, sales description).
- **Multilingual Support:** Supports instant copywriting and translation in 6 languages:
  - 🇺🇸 English (Global)
  - 🇹🇭 Thai (ภาษาไทย)
  - 🇯🇵 Japanese (日本語)
  - 🇨🇳 Chinese (中文)
  - 🇩🇪 German (Deutsch)
  - 🇫🇷 French (Français)
- **Copywriting Tone Selection:**
  - **Persuasive & Marketing-Driven:** Focuses on emotional hooks, benefits, and conversions.
  - **Technical & Specification-Focused:** Focuses on precise technical details, dimensions, and specifications.
  - **Luxury & Premium:** Sophisticated language emphasizing craftsmanship and exclusivity.
  - **Casual & Engaging:** Friendly, conversational tone for lifestyle products.
- **Asynchronous Batch Processing:** Mass-enrich multiple products in the background via the job queue.
- **Chatter Change Logs:** Automatically posts an audit summary of applied AI enrichments to the product's chatter history.

---

## 🛠️ Single Product Enrichment Workflow

### Step 1: Open Target Product
Navigate to **Inventory / Sales > Products** and open any product template (e.g. *Acoustic Noise-Canceling Headphones*).

### Step 2: Launch the Enrichment Wizard
Click the **"Enrich with Hermes"** button located in the form view header.

```
+-----------------------------------------------------------------------------+
| Product Template: Acoustic Noise-Canceling Headphones                       |
| [ Enrich with Hermes ] [ Update Quantity ] [ Print Labels ]                 |
+-----------------------------------------------------------------------------+
```

### Step 3: Configure Tone & Target Language
In the popup modal:
1. Select your target **Copywriting Tone** (e.g. *Persuasive & Marketing-Driven*).
2. Select your **Target Language** (e.g. *English* or *Thai*).
3. Toggle the checkboxes for the fields you wish to generate:
   - `[x]` Apply SEO Title & Meta Description
   - `[x]` Apply Key Highlights & Bullet Points
   - `[x]` Apply Formatted Sales Description
4. Click **"Generate AI Preview"**.

### Step 4: Inspect Side-by-Side Diff Preview
The wizard displays three tabs with side-by-side before/after previews:
- **SEO & Meta Details:** Current product title vs proposed 60-character SEO title, high-intent keywords, and meta description.
- **Key Highlights & Specs:** Formatted bullet points highlighting top benefits.
- **Formatted Description:** Rich HTML product description formatted for web and eCommerce.

```
+-----------------------------------------------------------------------------+
| Current Description                    | Proposed AI Description            |
|----------------------------------------+------------------------------------|
| Standard black headphones with mic.    | <p>Experience world-class audio... |
| Battery lasts a while.                 | <ul><li>30hr battery</li>...</ul>  |
+-----------------------------------------------------------------------------+
```

### Step 5: Apply Changes
- If satisfied, click **"Apply Selected Changes"**.
- To try another angle, adjust the tone or prompt and click **"Regenerate Preview"**.

---

## 📦 Batch Mass-Enrichment Workflow

To enrich dozens or hundreds of products in bulk:

1. Navigate to **Inventory / Sales > Products** in list view.
2. Select multiple product records using the checkboxes.
3. Click the **Action** dropdown menu at the top and select **"Enrich with Hermes"**.
4. Configure your desired **Tone** and **Language**.
5. Click **"Enqueue Batch Job"**.
6. The system creates an asynchronous job in `ai_ce.job` and processes records in the background without locking your user session.
7. Track live progress in **AI Hub > Agentic Operations > Background Jobs**.

---

## 📊 Technical Fields Added to `product.template`

| Technical Field | Type | Description |
|---|---|---|
| `ai_seo_title` | Char | Search engine optimized title tag (60-70 chars). |
| `ai_seo_description` | Text | Search engine snippet description (150-160 chars). |
| `ai_seo_keywords` | Char | Comma-separated high-intent search keywords. |
| `ai_feature_bullets` | Html | Bullet points of key specifications and selling points. |
| `ai_enriched_description` | Html | Formatted eCommerce marketing copy. |
| `ai_last_enriched` | Datetime | Timestamp of last AI catalog update. |
| `ai_enrich_status` | Selection | `draft` (Not Enriched), `in_progress`, or `enriched`. |
