# Hermes Content Studio Guide

The **Hermes Content Studio (`ai_ce.content.studio.wizard`)** is a centralized omni-channel copywriting and content creation suite. It crafts tailored content across marketing emails, LINE messaging channels, knowledge articles, and social networks with formatting customized for each platform.

---

## 🎨 Supported Omni-Channels

| Channel | Output Format | Use Case |
|---|---|---|
| 📧 **Marketing Email Campaign** | Responsive HTML Body + Subject + Preheader | Email marketing newsletters and mass mailings via `mass_mailing`. |
| 💬 **LINE Bot Broadcast** | Short Conversational Text + Structured LINE Flex Message JSON | Promotional broadcasts and interactive cards for LINE messaging (`odoo_line_bot`). |
| 📚 **Knowledge Base & Blog Article** | Long-Form Markdown / HTML with Heading Hierarchy & FAQs | Documentation, user manuals, and corporate blog articles. |
| 📱 **Social Media Blurbs** | Multi-Platform Copy with Emojis & Hashtags | LinkedIn announcements, Twitter/X posts, and Instagram captions. |
| ✍️ **General Sales Copy** | Value Proposition & Sales Pitch | Customer quotations, proposals, and CRM sales collateral. |

---

## 🛠️ Step-by-Step Guide

### Step 1: Launch the Content Studio
- From the Main Menu: Go to **AI Hub > Agentic Operations > Hermes Content Studio**.
- Or from any document: Open an existing Mass Mailing campaign, LINE Broadcast wizard, or Product record and click **"Content Studio"**.

### Step 2: Define Campaign Parameters
Fill in the guided prompt fields:
1. **Target Omni-Channel:** Select your delivery channel (e.g. *Marketing Email Campaign* or *LINE Bot Broadcast*).
2. **Campaign Topic / Title:** Enter the primary subject (e.g. *Summer Flash Sale Promotion* or *Quarterly Product Release*).
3. **Target Audience:** Define your target persona (e.g. *Existing B2B Retailers* or *VIP Loyalty Members*).
4. **Primary Goal & Call-to-Action (CTA):** Specify what action the recipient should take (e.g. *Use 20% discount code SUMMER20* or *Schedule a 15-minute consultation*).
5. **Tone of Voice:** Select from *Persuasive & High-Conversion*, *Urgent (FOMO)*, *Polished Professional B2B*, *Excited & Friendly*, or *Storytelling*.
6. **Language:** Select language (English, Thai, Japanese, Chinese, German, French).

### Step 3: Generate Content
Click **"Craft Content with Hermes"**. The AI engine drafts tailored content according to the selected channel's formatting constraints.

### Step 4: Preview & Direct Injection
Depending on the channel selected, inspect the output tabs:
- **Headline & Subject:** High-converting subject line and preheader subtitle.
- **Responsive HTML Preview:** Rendered HTML email body with styled CTA buttons.
- **LINE Flex Message JSON:** Valid LINE Flex Message JSON bubble ready for instant broadcast.
- **Markdown / Article Copy:** Long-form article with structured sections.

Click **"Inject into Document"** to write the generated copy directly into your active Mass Mailing campaign, LINE account, or Product description without copy-pasting.

---

## 💡 Example Outputs

### LINE Flex Message JSON Payload Example
```json
{
  "type": "bubble",
  "hero": {
    "type": "image",
    "url": "https://example.com/banner.jpg",
    "size": "full",
    "aspectRatio": "20:13",
    "aspectMode": "cover"
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "🔥 Flash Sale Alert!",
        "weight": "bold",
        "size": "xl"
      },
      {
        "type": "text",
        "text": "Get 20% off all catalog items this weekend only. Use code SUMMER20.",
        "wrap": true,
        "color": "#666666",
        "margin": "md"
      }
    ]
  },
  "footer": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "button",
        "style": "primary",
        "color": "#0284c7",
        "action": {
          "type": "uri",
          "label": "Shop Now",
          "uri": "https://example.com/shop"
        }
      }
    ]
  }
}
```
