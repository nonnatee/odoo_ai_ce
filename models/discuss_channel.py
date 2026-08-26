# -*- coding: utf-8 -*-
import json
import logging
import re
from odoo import models, fields, api, tools, _
from odoo.tools import html2plaintext

try:
    from markupsafe import Markup, escape
except ImportError:
    try:
        from odoo.tools import Markup, escape
    except ImportError:
        def Markup(s): return s
        def escape(s): return s

_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _register_hook(self):
        """Pre-initialize AI partner and AI user on startup so they are discoverable in Discuss and chatter."""
        super()._register_hook()
        try:
            self._get_ai_partner()
            self._get_ai_user()
        except Exception as e:
            _logger.debug("Could not pre-initialize AI identity in _register_hook: %s", e)

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
    def _get_ai_user(self):
        """
        Safely retrieve or dynamically create the dedicated AI Assistant user (res.users)
        bound to the Hermes AI Agent partner (mirroring OdooBot base.user_root / base.partner_root).
        """
        user = self.env.ref('odoo_ai_ce.user_ai_assistant', raise_if_not_found=False)
        if user and user.exists():
            if not user.active:
                user.sudo().write({'active': True})
            return user

        partner = self._get_ai_partner()
        if not partner:
            return self.env.user

        # Search existing user by login or partner_id
        user = self.env['res.users'].sudo().search([
            '|', ('login', '=', 'hermes.ai@odoo.internal'), ('partner_id', '=', partner.id)
        ], limit=1)
        if user:
            if not user.active:
                user.sudo().write({'active': True})
            self._bind_user_xmlid(user)
            return user

        # Create res.users record bound to partner
        try:
            with self.env.cr.savepoint():
                user_vals = {
                    'name': partner.name or 'Hermes AI Agent',
                    'login': 'hermes.ai@odoo.internal',
                    'partner_id': partner.id,
                    'active': True,
                    'share': False,
                    'notification_type': 'in_box',
                }
                user = self.env['res.users'].sudo().create(user_vals)
                self._bind_user_xmlid(user)
                return user
        except Exception as e:
            _logger.warning("Could not create dedicated AI user (%s); falling back to base.user_root", e)
            return self.env.ref('base.user_root', raise_if_not_found=False) or self.env.user

    @api.model
    def _bind_user_xmlid(self, user):
        data = self.env['ir.model.data'].sudo().search([
            ('module', '=', 'odoo_ai_ce'),
            ('name', '=', 'user_ai_assistant'),
        ], limit=1)
        if not data:
            try:
                self.env['ir.model.data'].sudo().create({
                    'module': 'odoo_ai_ce',
                    'name': 'user_ai_assistant',
                    'model': 'res.users',
                    'res_id': user.id,
                    'noupdate': True,
                })
            except Exception:
                pass
        elif data.res_id != user.id:
            try:
                data.write({'res_id': user.id})
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
                welcome_html = Markup(
                    "<p>👋 <strong>Hello %s!</strong></p>"
                    "<p>I am <strong>Hermes AI Agent</strong>, your sovereign autonomous assistant embedded in Odoo ERP.</p>"
                    "<p>You can ask me questions about your database (Sales, CRM, Invoices, Products), "
                    "request document summaries, or give me operational tasks. How can I help you today?</p>"
                ) % escape(user_partner.name or "there")

                channel.sudo().with_context(
                    mail_create_nosubscribe=True,
                    mail_post_autofollow=False,
                    mail_notify_author=False
                ).message_post(
                    body=welcome_html,
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

    @api.model
    @tools.ormcache()
    def _get_cached_ai_partner_id(self):
        """Return the cached ID of the AI Assistant partner (0 SQL queries on hot path)."""
        partner = self._get_ai_partner()
        return partner.id if partner else False

    def _message_post_after_hook(self, message, msg_vals):
        """
        Intercept Discuss messages to trigger the AI Agent if the AI Bot partner is mentioned
        or participating in a direct chat. (Optimized with OdooBot fast-path short-circuiting)
        """
        super()._message_post_after_hook(message, msg_vals)

        # Fast-path 1: Ignore empty or non-conversational messages
        if not message or not message.body:
            return
        if message.message_type not in ('comment', 'email'):
            return

        ai_partner_id = self._get_cached_ai_partner_id()
        if not ai_partner_id:
            return

        # Fast-path 2: Avoid recursion if message was posted by the AI bot itself
        if message.author_id.id == ai_partner_id:
            return

        # Fast-path 3: Check if AI partner is mentioned or in a direct chat channel
        is_mentioned = ai_partner_id in message.partner_ids.ids
        is_direct_chat = (
            getattr(self, 'channel_type', '') == 'chat'
            and (
                ai_partner_id in getattr(self, 'channel_partner_ids', self.env['res.partner']).ids
                or ai_partner_id in self.mapped('channel_member_ids.partner_id').ids
            )
        )

        if is_mentioned or is_direct_chat:
            ai_partner = self.env['res.partner'].browse(ai_partner_id)
            self._dispatch_ai_agent_turn(message, ai_partner)

    def _try_fast_path_command(self, prompt, ai_partner, session):
        """
        Fast-Path Slash Command Handler (OdooBot Pattern).
        Executes instant operational queries in 0ms without consuming LLM tokens.
        """
        lower = prompt.strip().lower()
        if not lower.startswith('/'):
            return None

        cmd = lower.split()[0]

        if cmd in ('/help', '/commands'):
            return Markup("""
<div class='o_ai_command_help'>
    <h6><i class='fa fa-terminal text-primary'></i> <strong>Hermes AI Agent Commands</strong></h6>
    <ul class='list-unstyled small mb-0'>
        <li><code>/status</code> - View active LLM provider, model, latency, and Sidecar IPC status.</li>
        <li><code>/tools</code> - List all active registered callable tools and consent gates.</li>
        <li><code>/models</code> - View all available LLM models in the catalog.</li>
        <li><code>/consent</code> - Check pending Human-in-the-Loop approval requests.</li>
        <li><code>/clear</code> - Reset active conversation memory for this channel.</li>
        <li><code>/help</code> - Show this command reference.</li>
    </ul>
    <p class='text-muted small mt-2 mb-0'>💡 <em>Or simply type any natural language request (e.g. "Search top 5 opportunities in CRM").</em></p>
</div>""")

        elif cmd in ('/status', '/ping'):
            provider = self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
            models_cnt = self.env['ai_ce.model'].search_count([])
            tools_cnt = self.env['ai_ce.tool'].search_count([('active', '=', True)])
            consents_cnt = self.env['ai_ce.consent'].search_count([('state', '=', 'pending')])
            provider_name = escape(provider.name) if provider else "None"
            prov_type = escape(provider.service.upper()) if provider else "-"

            return Markup(f"""
<div class='o_ai_status_card p-2'>
    <h6><i class='fa fa-heartbeat text-success'></i> <strong>Hermes AI System Status</strong></h6>
    <table class='table table-sm table-borderless small mb-0'>
        <tr><td><strong>Active Provider:</strong></td><td><span class='badge bg-primary'>{provider_name} ({prov_type})</span></td></tr>
        <tr><td><strong>Catalog Models:</strong></td><td>{models_cnt} models available</td></tr>
        <tr><td><strong>Callable Tools:</strong></td><td>{tools_cnt} registered tools</td></tr>
        <tr><td><strong>Pending Approvals:</strong></td><td><span class='badge bg-{"warning" if consents_cnt > 0 else "success"}'>{consents_cnt} pending</span></td></tr>
        <tr><td><strong>Channel Session:</strong></td><td>Session #{session.id} ({session.message_count} messages)</td></tr>
    </table>
</div>""")

        elif cmd == '/tools':
            tools = self.env['ai_ce.tool'].search([('active', '=', True)], limit=15)
            tool_rows = "".join([
                f"<tr><td><code>{escape(t.name)}</code></td><td>{'<span class=\"badge bg-warning text-dark\">HITL Gated</span>' if t.requires_user_consent else '<span class=\"badge bg-success\">Auto</span>'}</td><td><small>{escape(t.description or '-')}</small></td></tr>"
                for t in tools
            ])
            return Markup(f"""
<div class='o_ai_tools_list'>
    <h6><i class='fa fa-wrench text-primary'></i> <strong>Active Callable Tools ({len(tools)})</strong></h6>
    <table class='table table-sm table-hover small'>
        <thead><tr><th>Tool Name</th><th>Safety</th><th>Description</th></tr></thead>
        <tbody>{tool_rows}</tbody>
    </table>
</div>""")

        elif cmd == '/models':
            models_rec = self.env['ai_ce.model'].search([], limit=10)
            rows = "".join([
                f"<tr><td><strong>{escape(m.name)}</strong></td><td><code>{escape(m.technical_name)}</code></td><td>{escape(m.provider_id.name or '-')}</td></tr>"
                for m in models_rec
            ])
            return Markup(f"""
<div class='o_ai_models_list'>
    <h6><i class='fa fa-cubes text-primary'></i> <strong>Available LLM Models</strong></h6>
    <table class='table table-sm table-hover small'>
        <thead><tr><th>Model Name</th><th>Technical ID</th><th>Provider</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
</div>""")

        elif cmd == '/consent':
            consents = self.env['ai_ce.consent'].search([('state', '=', 'pending')], limit=5)
            if not consents:
                return Markup("<p class='text-success mb-0'><i class='fa fa-check-circle'></i> All Clear: No pending consent approvals in the queue.</p>")
            rows = "".join([
                f"<li><strong>#{c.id}</strong> - Tool: <code>{escape(c.tool_id.name)}</code> (Requested by: {escape(c.user_id.name)})</li>"
                for c in consents
            ])
            return Markup(f"""
<div class='alert alert-warning mb-0'>
    <strong><i class='fa fa-shield'></i> Pending Approvals ({len(consents)}):</strong>
    <ul class='small mb-0 mt-1'>{rows}</ul>
    <small class='d-block mt-1'>Go to <strong>AI Hub > Agentic Operations > Pending Approvals</strong> to confirm or reject.</small>
</div>""")

        elif cmd == '/clear':
            session.clear_history()
            return Markup(f"<p class='text-info mb-0'><i class='fa fa-trash'></i> Conversation session #{session.id} history has been cleared.</p>")

        return None

    def _format_ai_response_html(self, text, pending_consent_id=None):
        """
        Format AI agent response text (converting markdown, code blocks, bullet points)
        into rich sanitized HTML wrapped in Markup for crisp rendering in Odoo Discuss.
        """
        if not text:
            text = _("I have processed your request.")

        # 1. Protect code blocks
        code_blocks = []
        def _sub_code_block(m):
            code_blocks.append(m.group(2).rstrip())
            return f"@@CODEBLOCK{len(code_blocks)-1}@@"
        formatted = re.sub(r'```([a-zA-Z0-9_\-\+]*)\r?\n([\s\S]*?)```', _sub_code_block, text)

        # 2. Protect inline code
        inline_codes = []
        def _sub_inline(m):
            inline_codes.append(m.group(1))
            return f"@@INLINECODE{len(inline_codes)-1}@@"
        formatted = re.sub(r'`([^`\n]+)`', _sub_inline, formatted)

        # 3. Escape HTML characters in user text
        formatted = str(escape(formatted))

        # 4. Bold & Italic
        formatted = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', formatted)
        formatted = re.sub(r'(^|[^\*])\*([^*\n]+)\*([^\*]|$)', r'\1<em>\2</em>\3', formatted)

        # 5. Bullet Lists
        formatted = re.sub(r'^(\s*)[-\*]\s+(.+)$', r'<li class="mb-1">\2</li>', formatted, flags=re.M)
        formatted = re.sub(r'((?:<li[^>]*>.*?</li>\s*)+)', r'<ul class="ps-3 my-2">\1</ul>', formatted, flags=re.S)

        # 6. Paragraphs and Line Breaks
        blocks = [b.strip() for b in re.split(r'\n\s*\n', formatted) if b.strip()]
        html_blocks = []
        for b in blocks:
            if b.startswith('<ul') or b.startswith('@@CODEBLOCK'):
                html_blocks.append(b)
            else:
                html_blocks.append(f"<p class='mb-2'>{b.replace(chr(10), '<br/>')}</p>")
        formatted = "".join(html_blocks)

        # 7. Restore Inline Code
        def _restore_inline(m):
            idx = int(m.group(1))
            code = str(escape(inline_codes[idx])) if idx < len(inline_codes) else ""
            return f"<code class='px-1 py-0.5 rounded bg-light text-primary font-monospace small'>{code}</code>"
        formatted = re.sub(r'@@INLINECODE(\d+)@@', _restore_inline, formatted)

        # 8. Restore Code Blocks
        def _restore_block(m):
            idx = int(m.group(1))
            code = str(escape(code_blocks[idx])) if idx < len(code_blocks) else ""
            return f"<pre class='p-2 my-2 bg-dark text-light rounded font-monospace small overflow-auto'><code>{code}</code></pre>"
        formatted = re.sub(r'@@CODEBLOCK(\d+)@@', _restore_block, formatted)

        # 9. Append HITL Consent Banner if pending
        if pending_consent_id:
            formatted += f"""
<div class='alert alert-warning mt-2 p-2 rounded'>
    <strong><i class='fa fa-shield'></i> Approval Required:</strong> 
    This action requires administrator confirmation. 
    Pending Consent Request <strong>#{pending_consent_id}</strong> has been queued.
</div>"""

        return Markup(f"<div class='o_ai_discuss_response'>{formatted}</div>")

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

        # 1. Fast-path indexed session retrieval
        session = self.env['ai_ce.session'].search([
            ('channel_id', '=', self.id)
        ], limit=1)
        if not session:
            session = self.env['ai_ce.session'].create({
                'name': f"Discuss Channel #{self.id}",
                'channel_id': self.id,
                'user_id': message.author_id.user_ids[:1].id or self.env.uid,
            })

        # 2. Fast-Path Command Handling (0ms / 0 Tokens)
        fast_reply = self._try_fast_path_command(prompt, ai_partner, session)
        if fast_reply:
            self.with_context(
                mail_create_nosubscribe=True,
                mail_post_autofollow=False,
                mail_notify_author=False
            ).message_post(
                body=fast_reply,
                author_id=ai_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            return

        # 3. Locate default or active agent
        agent = self.env['ai_ce.agent'].search([('active', '=', True)], limit=1)
        if not agent:
            provider = self.env['ai_ce.provider'].search([('active', '=', True)], order='priority asc', limit=1)
            if not provider:
                self.with_context(
                    mail_create_nosubscribe=True,
                    mail_post_autofollow=False,
                    mail_notify_author=False
                ).message_post(
                    body=Markup("<p class='text-danger'>⚠️ No AI Provider is configured or active. Please configure an AI Provider in Settings.</p>"),
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

            body_html = self._format_ai_response_html(answer, pending_consent_id)

            self.with_context(
                mail_create_nosubscribe=True,
                mail_post_autofollow=False,
                mail_notify_author=False
            ).message_post(
                body=body_html,
                author_id=ai_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

        except Exception as e:
            _logger.exception("Error executing AI turn in discuss channel %s", self.id)
            self.with_context(
                mail_create_nosubscribe=True,
                mail_post_autofollow=False,
                mail_notify_author=False
            ).message_post(
                body=Markup(f"<p class='text-danger'>❌ Error executing AI Agent turn: {escape(str(e))}</p>"),
                author_id=ai_partner.id,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
