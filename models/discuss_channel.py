# -*- coding: utf-8 -*-
import json
import logging
import re
from odoo import models, api, _
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _message_post_after_hook(self, message, msg_vals):
        """
        Intercept Discuss messages to trigger the AI Agent if the AI Bot partner is mentioned
        or participating in a direct chat.
        """
        super()._message_post_after_hook(message, msg_vals)

        ai_partner = self.env.ref('odoo_ai_ce.partner_ai_assistant', raise_if_not_found=False)
        if not ai_partner:
            return

        # Avoid recursion if message was posted by the AI bot itself
        if message.author_id.id == ai_partner.id:
            return

        # Check if AI partner is mentioned or in a direct chat channel
        is_mentioned = ai_partner in message.partner_ids
        is_direct_chat = (
            getattr(self, 'channel_type', '') == 'chat'
            and ai_partner in getattr(self, 'channel_partner_ids', self.env['res.partner'])
        )

        if is_mentioned or is_direct_chat:
            self._dispatch_ai_agent_turn(message, ai_partner)

    def _dispatch_ai_agent_turn(self, message, ai_partner):
        """
        Execute an agent turn and post the AI response back into this Discuss channel.
        """
        self.ensure_one()
        raw_text = html2plaintext(message.body or "").strip()
        if not raw_text:
            return

        # Clean mention text (e.g. "@Hermes AI Agent" or "@Hermes")
        prompt = re.sub(r'@[\w\s]+', '', raw_text).strip() or raw_text

        # Find or create a conversation session for this discuss channel
        session = self.env['ai_ce.session'].search([
            ('name', '=', f"Discuss Channel #{self.id}")
        ], limit=1)
        if not session:
            session = self.env['ai_ce.session'].create({
                'name': f"Discuss Channel #{self.id}",
                'user_id': message.author_id.user_ids[:1].id or self.env.uid,
            })

        # Locate default or active agent
        agent = self.env['ai_ce.agent'].search([('active', '=', True)], limit=1)
        if not agent:
            provider = self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
            if not provider:
                self.message_post(
                    body=_("<p class='text-danger'>⚠️ No AI Provider is configured or active. Please configure an AI Provider in Settings.</p>"),
                    author_id=ai_partner.id,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
                return
            agent = self.env['ai_ce.agent'].create({
                'name': 'Hermes Autonomous Agent',
                'provider_id': provider.id,
                'tool_ids': [(6, 0, self.env['ai_ce.tool'].search([('active', '=', True)]).ids)],
            })

        caller_uid = message.author_id.user_ids[:1].id or self.env.uid

        try:
            result = agent.run_agent(
                user_prompt=prompt,
                session=session,
                record_context={'discuss_channel_id': self.id, 'channel_name': self.name},
                user_id=caller_uid,
            )
            answer = result.get('answer') or _("I have processed your request.")
            pending_consent_id = result.get('pending_consent_id')

            # Format answer with styling
            body_html = f"<div class='o_ai_discuss_response'>{answer}</div>"
            if pending_consent_id:
                body_html += f"""
<div class='alert alert-warning mt-2 p-2'>
    <strong><i class='fa fa-shield'></i> Approval Required:</strong> 
    This action requires administrator confirmation. 
    Pending Consent Request <strong>#{pending_consent_id}</strong> has been queued.
</div>"""

            self.message_post(
                body=body_html,
                author_id=ai_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

        except Exception as e:
            _logger.exception("Error executing AI turn in discuss channel %s", self.id)
            self.message_post(
                body=f"<p class='text-danger'>❌ Error executing AI Agent turn: {str(e)}</p>",
                author_id=ai_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
