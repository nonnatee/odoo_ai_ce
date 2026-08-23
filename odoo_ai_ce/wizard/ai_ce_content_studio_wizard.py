# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeContentStudioWizard(models.TransientModel):
    _name = "ai_ce.content.studio.wizard"
    _description = "Unified Hermes Omni-Channel Content Studio"

    channel = fields.Selection([
        ('email', '📧 Marketing Email Campaign (mass_mailing)'),
        ('line', '💬 LINE Bot Broadcast (Flex Message)'),
        ('knowledge', '📚 Knowledge Base / Blog Article'),
        ('social', '📱 Social Media & Promotional Blurb'),
        ('general', '✍️ General Copywriting & Sales Pitch'),
    ], string="Target Omni-Channel", default='email', required=True)

    topic = fields.Char(string="Campaign Topic / Title", required=True, placeholder="e.g. Summer Mega Sale, New Product Launch")
    target_audience = fields.Char(string="Target Audience", default="Existing Customers & Subscribers", placeholder="e.g. VIP B2B Buyers, Tech Enthusiasts")
    campaign_goal = fields.Char(string="Primary Goal & CTA", default="Drive website purchases with 20% discount code SUMMER20", placeholder="e.g. Book a live demo, Claim discount")

    tone = fields.Selection([
        ('Persuasive', 'Persuasive & High-Conversion'),
        ('Urgent', 'Urgent & Time-Sensitive (FOMO)'),
        ('Professional', 'Polished & Professional B2B'),
        ('Excited', 'Energetic, Friendly & Casual'),
        ('Storytelling', 'Inspiring & Narrative-Driven'),
    ], string="Tone of Voice", default='Persuasive', required=True)

    language = fields.Selection([
        ('EN', 'English'),
        ('TH', 'Thai (ภาษาไทย)'),
        ('JA', 'Japanese (日本語)'),
        ('ZH', 'Chinese (中文)'),
        ('DE', 'German (Deutsch)'),
        ('FR', 'French (Français)'),
    ], string="Language", default='EN', required=True)

    # Generated Output Fields
    generated_subject = fields.Char(string="Generated Subject / Headline")
    generated_preheader = fields.Char(string="Generated Preheader / Subtitle")
    generated_body_html = fields.Html(string="Generated Responsive HTML")
    generated_line_flex = fields.Text(string="Generated LINE Flex JSON Payload")
    generated_markdown = fields.Text(string="Generated Markdown / Text")

    is_generated = fields.Boolean(string="Content Ready", default=False)
    res_model = fields.Char(string="Source Model")
    res_id = fields.Integer(string="Source Record ID")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')

        res['res_model'] = active_model
        res['res_id'] = active_id

        if active_model == 'mailing.mailing' or active_model == 'mass.mailing':
            res['channel'] = 'email'
        elif active_model in ('line.account', 'line.push.wizard'):
            res['channel'] = 'line'
        elif active_model in ('knowledge.article', 'blog.post'):
            res['channel'] = 'knowledge'
        elif active_model == 'product.template' and active_id:
            product = self.env['product.template'].browse(active_id)
            res['topic'] = f"Promotional Spotlight: {product.name}"
        return res

    def action_generate_content(self):
        """Invoke LLM Provider to craft multi-channel structured content."""
        self.ensure_one()
        provider = self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
        if not provider:
            raise UserError(_("No active AI Provider configured in Settings."))

        channel_prompt_map = {
            'email': "Generate a high-converting marketing email with an eye-catching subject line, preview preheader, engaging story, clear benefit bullets, and prominent HTML Call-To-Action button.",
            'line': "Generate a LINE promotional message: short conversational message (under 300 chars) AND a valid LINE Flex Message JSON bubble with header, hero image placeholder, body specs, and action button.",
            'knowledge': "Generate an in-depth Knowledge Article in Markdown format: Title, Executive Summary, 3 Detailed Sections with bullet points, Best Practices, and FAQ section.",
            'social': "Generate 3 social media variations (LinkedIn, Twitter/X, Instagram) with engaging hooks, emojis, and relevant hashtags.",
            'general': "Generate persuasive sales copy and value proposition overview."
        }

        prompt = f"""
You are a world-class copywriter and omni-channel marketing strategist.
Create compelling content for:
Channel: {self.channel} ({channel_prompt_map.get(self.channel, '')})
Topic: {self.topic}
Target Audience: {self.target_audience}
Goal & Call-to-Action: {self.campaign_goal}
Tone: {self.tone}
Language: {self.language}

Respond STRICTLY with a valid JSON object matching this schema:
{{
    "subject": "Headline or Email Subject Line",
    "preheader": "Short subtitle or email preheader",
    "body_html": "<div style='font-family: sans-serif; padding: 20px;'><h2>Compelling Headline</h2><p>Body copy...</p><a href='#' style='background:#0284c7; color:#fff; padding:10px 20px; border-radius:5px; text-decoration:none;'>CTA Button</a></div>",
    "line_flex_json": "{{\\"type\\": \\"bubble\\", \\"body\\": {{\\"type\\": \\"box\\", \\"layout\\": \\"vertical\\", \\"contents\\": [{{\\"type\\": \\"text\\", \\"text\\": \\"Promo Title\\", \\"weight\\": \\"bold\\"}}]}}}}",
    "markdown_content": "# Title\\n\\n## Summary\\n..."
}}
"""
        messages = [
            {"role": "system", "content": "You are Hermes Content Studio AI. You output ONLY JSON."},
            {"role": "user", "content": prompt}
        ]

        response = provider.chat(messages=messages, temperature=0.4)
        content = response.get('content', '').strip()

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            data = json.loads(content.strip())
        except Exception as e:
            _logger.error("Failed to parse Content Studio JSON: %s\nRaw: %s", e, content)
            data = {
                "subject": f"Special Update: {self.topic}",
                "preheader": f"Discover our latest update on {self.topic}",
                "body_html": f"<h2>{self.topic}</h2><p>{self.campaign_goal}</p>",
                "line_flex_json": "{}",
                "markdown_content": f"# {self.topic}\n\n{self.campaign_goal}"
            }

        self.write({
            'generated_subject': data.get('subject', ''),
            'generated_preheader': data.get('preheader', ''),
            'generated_body_html': data.get('body_html', ''),
            'generated_line_flex': data.get('line_flex_json', '') if isinstance(data.get('line_flex_json'), str) else json.dumps(data.get('line_flex_json', {}), indent=2),
            'generated_markdown': data.get('markdown_content', ''),
            'is_generated': True,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_inject_to_target(self):
        """Inject generated copy directly into active document (mailing, LINE wizard, knowledge)."""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise UserError(_("No active document bound for direct injection."))

        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            raise UserError(_("Target record no longer exists."))

        if self.res_model in ('mailing.mailing', 'mass.mailing'):
            vals = {}
            if self.generated_subject:
                vals['subject'] = self.generated_subject
            if self.generated_body_html:
                vals['body_html'] = self.generated_body_html
            if hasattr(record, 'preview') and self.generated_preheader:
                vals['preview'] = self.generated_preheader
            record.write(vals)

        elif self.res_model == 'product.template':
            if self.generated_body_html:
                record.write({
                    'ai_enriched_description': self.generated_body_html,
                    'description_sale': self.generated_body_html
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Content Injected"),
                'message': _("Hermes content successfully injected into %s.") % record.display_name,
                'type': 'success',
                'sticky': False,
            }
        }
