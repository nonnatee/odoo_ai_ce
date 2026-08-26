# -*- coding: utf-8 -*-
import json
import logging
import re
from odoo import models, api, _
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _register_hook(self):
        """Pre-initialize AI partner on startup so it is immediately discoverable in Discuss."""
        super()._register_hook()
        try:
            self._get_ai_partner()
        except Exception as e:
            _logger.debug("Could not pre-initialize AI partner in _register_hook: %s", e)

    @api.model
    def _get_ai_partner(self):
        """
        Safely retrieve or dynamically create the AI Assistant partner record
        without breaking on third-party custom required fields or constraints on res.partner.
        """
        partner = self.env.ref('odoo_ai_ce.partner_ai_assistant', raise_if_not_found=False)
        if partner and partner.exists():
            if not partner.active:
                partner.sudo().write({'active': True})
            return partner

        # Search existing partner by name or email
        partner = self.env['res.partner'].sudo().search([
            '|', ('name', '=', 'Hermes AI Agent'), ('email', '=', 'hermes.ai@odoo.internal')
        ], limit=1)
        if partner:
            if not partner.active:
                partner.sudo().write({'active': True})
            self._bind_partner_xmlid(partner)
            return partner

        # Attempt to create partner dynamically with default_get + required field fallbacks
        Partner = self.env['res.partner'].sudo()
        try:
            vals = Partner.default_get(list(Partner._fields.keys()))
            vals.update({
                'name': 'Hermes AI Agent',
                'email': 'hermes.ai@odoo.internal',
                'active': True,
                'is_company': False,
                'type': 'contact',
                'comment': 'Virtual Autonomous AI Assistant powered by Hermes ACP & odoo_ai_ce',
            })
            if 'im_status' in Partner._fields:
                vals['im_status'] = 'bot'

            # Auto-populate any missing required fields to prevent DB NOT NULL constraints
            for fname, field in Partner._fields.items():
                if fname not in vals and getattr(field, 'required', False):
                    if field.type == 'boolean':
                        vals[fname] = False
                    elif field.type in ('integer', 'float', 'monetary'):
                        vals[fname] = 0
                    elif field.type == 'selection':
                        sel = field.selection
                        if callable(sel):
                            sel = sel(Partner)
                        if sel:
                            vals[fname] = sel[0][0]
                    elif field.type in ('char', 'text', 'html'):
                        vals[fname] = '-'

            with self.env.cr.savepoint():
                partner = Partner.create(vals)
                self._bind_partner_xmlid(partner)
                return partner
        except Exception as e:
            _logger.warning(
                "Could not create dedicated AI partner due to res.partner constraints (%s); falling back to base.partner_root",
                e
            )
            return self.env.ref('base.partner_root', raise_if_not_found=False) or self.env.user.partner_id

    @api.model
    def _bind_partner_xmlid(self, partner):
        data = self.env['ir.model.data'].sudo().search([
            ('module', '=', 'odoo_ai_ce'),
            ('name', '=', 'partner_ai_assistant'),
        ], limit=1)
        if not data:
            try:
                self.env['ir.model.data'].sudo().create({
                    'module': 'odoo_ai_ce',
                    'name': 'partner_ai_assistant',
                    'model': 'res.partner',
                    'res_id': partner.id,
                    'noupdate': True,
                })
            except Exception:
                pass
        elif data.res_id != partner.id:
            try:
                data.write({'res_id': partner.id})
            except Exception:
                pass

    @api.model
    def action_open_ai_discuss_chat(self):
        """
        Find or create a direct 1-on-1 chat channel between the current user and Hermes AI Agent
        and return an action to immediately open Discuss focused on this conversation.
        """
        ai_partner = self._get_ai_partner()
        user_partner = self.env.user.partner_id
        if not ai_partner or not user_partner:
            return False

        # Search for existing 1-on-1 chat
        channel = False
        member_model = self.env.get('discuss.channel.member')
        if member_model is not None:
            user_channels = member_model.sudo().search([
                ('partner_id', '=', user_partner.id)
            ]).mapped('channel_id').filtered(lambda c: c.channel_type == 'chat')

            for c in user_channels:
                members = c.mapped('channel_member_ids.partner_id').ids or c.mapped('channel_partner_ids').ids
                if ai_partner.id in members:
                    channel = c
                    break

        if not channel:
            channels = self.sudo().search([('channel_type', '=', 'chat')])
            for c in channels:
                members = c.mapped('channel_member_ids.partner_id').ids or c.mapped('channel_partner_ids').ids
                if user_partner.id in members and ai_partner.id in members:
                    channel = c
                    break

        is_new = False
        if not channel:
            is_new = True
            # Try channel_get first (standard Odoo 17/18/19 way)
            try:
                if hasattr(self, 'channel_get'):
                    res = self.with_user(self.env.user).channel_get(partners_to=[ai_partner.id])
                    channel = self.sudo().browse(res.get('id')) if isinstance(res, dict) else res
            except Exception as e:
                _logger.warning("channel_get failed (%s); falling back to direct creation", e)

            # Fallback to direct creation with channel_member_ids
            if not channel:
                try:
                    channel = self.sudo().create({
                        'name': f"{user_partner.name}, {ai_partner.name}",
                        'channel_type': 'chat',
                        'channel_member_ids': [
                            (0, 0, {'partner_id': user_partner.id}),
                            (0, 0, {'partner_id': ai_partner.id}),
                        ],
                    })
                except Exception as e:
                    _logger.warning("Failed creating with channel_member_ids (%s); trying manual member insertion", e)
                    channel = self.sudo().create({
                        'name': f"{user_partner.name}, {ai_partner.name}",
                        'channel_type': 'chat',
                    })
                    if member_model is not None and channel:
                        member_model.sudo().create([
                            {'channel_id': channel.id, 'partner_id': user_partner.id},
                            {'channel_id': channel.id, 'partner_id': ai_partner.id},
                        ])

        if channel and is_new:
            try:
                channel.sudo().message_post(
                    body=_(
                        "<p>👋 <strong>Hello %s!</strong></p>"
                        "<p>I am <strong>Hermes AI Agent</strong>, your sovereign autonomous assistant embedded in Odoo ERP.</p>"
                        "<p>You can ask me questions about your database (Sales, CRM, Invoices, Products), "
                        "request document summaries, or give me operational tasks. How can I help you today?</p>"
                    ) % user_partner.name,
                    author_id=ai_partner.id,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
            except Exception as e:
                _logger.warning("Could not post welcome message in discuss channel: %s", e)

        # Open Discuss App focused on this channel
        try:
            action = self.env['ir.actions.actions']._for_xml_id('mail.action_discuss')
            action['context'] = {
                'active_id': channel.id,
                'default_active_id': f'discuss.channel_{channel.id}',
            }
            action['params'] = {
                'default_active_id': f'discuss.channel_{channel.id}',
            }
            return action
        except Exception:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Discuss',
                'res_model': 'discuss.channel',
                'res_id': channel.id,
                'view_mode': 'form',
                'views': [[False, 'form']],
                'target': 'current',
            }

    def _message_post_after_hook(self, message, msg_vals):
        """
        Intercept Discuss messages to trigger the AI Agent if the AI Bot partner is mentioned
        or participating in a direct chat.
        """
        super()._message_post_after_hook(message, msg_vals)

        ai_partner = self._get_ai_partner()
        if not ai_partner:
            return

        # Avoid recursion if message was posted by the AI bot itself
        if message.author_id.id == ai_partner.id:
            return

        # Check if AI partner is mentioned or in a direct chat channel
        is_mentioned = ai_partner in message.partner_ids
        is_direct_chat = (
            getattr(self, 'channel_type', '') == 'chat'
            and (
                ai_partner in getattr(self, 'channel_partner_ids', self.env['res.partner'])
                or ai_partner in self.mapped('channel_member_ids.partner_id')
            )
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
