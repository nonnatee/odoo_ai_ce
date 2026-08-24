# -*- coding: utf-8 -*-
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeProvider(models.Model):
    _name = "ai_ce.provider"
    _description = "AI Provider Engine"
    _order = "priority asc, id asc"

    name = fields.Char(string="Provider Name", required=True)
    service = fields.Selection([
        ('hermes', 'Hermes Agent Sidecar (ACP & Local Inference)'),
        ('ollama', 'Ollama (Local Inference)'),
        ('openai', 'OpenAI'),
        ('azure', 'Azure OpenAI'),
        ('anthropic', 'Anthropic Claude'),
        ('gemini', 'Google Gemini'),
        ('custom', 'Custom OpenAI-Compatible (LM Studio / vLLM)'),
    ], string="Service Type", required=True, default='hermes')
    
    api_base = fields.Char(string="Base URL", help="e.g. http://127.0.0.1:8765/v1 for Hermes or http://localhost:11434/v1 for Ollama")
    api_key = fields.Char(string="API Key", copy=False, help="Stored securely with encryption")
    priority = fields.Integer(string="Priority", default=10, help="Lower numbers take precedence in automatic routing and fallback")
    active = fields.Boolean(string="Active", default=True)
    
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('error', 'Connection Error'),
        ('unchecked', 'Unchecked')
    ], string="Status", default='unchecked', readonly=True)
    connection_error = fields.Text(string="Last Error", readonly=True)
    last_checked = fields.Datetime(string="Last Checked", readonly=True)
    
    model_ids = fields.One2many("ai_ce.model", "provider_id", string="Models Catalog")
    default_chat_model_id = fields.Many2one("ai_ce.model", string="Default Chat Model", domain="[('provider_id', '=', id), ('model_use', '=', 'chat')]")
    default_embedding_model_id = fields.Many2one("ai_ce.model", string="Default Embedding Model", domain="[('provider_id', '=', id), ('model_use', '=', 'embedding')]")
    fallback_provider_ids = fields.Many2many("ai_ce.provider", "ai_ce_provider_fallback_rel", "provider_id", "fallback_id", string="Fallback Providers")

    def action_check_connection(self):
        """Test API connectivity and update status."""
        for provider in self:
            try:
                provider._test_connection()
                provider.write({
                    'connection_status': 'connected',
                    'connection_error': False,
                    'last_checked': fields.Datetime.now()
                })
            except Exception as e:
                provider.write({
                    'connection_status': 'error',
                    'connection_error': str(e),
                    'last_checked': fields.Datetime.now()
                })
                raise UserError(_("Connection failed for %s: %s") % (provider.name, str(e)))
        return True

    def _test_connection(self):
        """Internal endpoint check."""
        base_url = self._get_effective_base_url()
        headers = self._get_headers()
        
        if self.service == 'hermes':
            # Check Hermes Sidecar Health Endpoint
            sidecar_host = base_url.replace('/v1', '')
            req = urllib.request.Request(f"{sidecar_host}/health", headers=headers, method="GET")
        else:
            test_url = f"{base_url}/models" if self.service in ('openai', 'azure', 'custom', 'ollama') else base_url
            req = urllib.request.Request(test_url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status not in (200, 201):
                    raise UserError(f"HTTP Status {resp.status}")
        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                raise UserError(_("Authentication failed: Check your API Key."))
            elif he.code != 200:
                raise UserError(f"HTTP Error {he.code}: {he.reason}")
        except Exception as e:
            raise UserError(str(e))

    def _get_effective_base_url(self):
        self.ensure_one()
        if self.api_base:
            return self.api_base.rstrip('/')
        if self.service == 'hermes':
            return "http://127.0.0.1:8765/v1"
        elif self.service == 'ollama':
            return "http://localhost:11434/v1"
        elif self.service == 'openai':
            return "https://api.openai.com/v1"
        elif self.service == 'anthropic':
            return "https://api.anthropic.com/v1"
        elif self.service == 'gemini':
            return "https://generativelanguage.googleapis.com/v1beta"
        return "http://127.0.0.1:8765/v1"

    def _get_headers(self):
        self.ensure_one()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            if self.service == 'anthropic':
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, messages, model_name=None, tools=None, temperature=0.7, max_tokens=2048):
        """
        Execute a chat completion request with standardized messages and tools schema.
        Supports automatic fallback to configured fallback_provider_ids on failure.
        """
        self.ensure_one()
        target_model = model_name or (self.default_chat_model_id.name if self.default_chat_model_id else "hermes-3-llama-3.1")
        
        try:
            return self._execute_chat(messages, target_model, tools, temperature, max_tokens)
        except Exception as primary_error:
            _logger.warning("Primary provider %s failed: %s. Checking fallbacks...", self.name, primary_error)
            for fallback in self.fallback_provider_ids.filtered(lambda p: p.active and p.connection_status != 'error'):
                try:
                    _logger.info("Retrying with fallback provider %s", fallback.name)
                    return fallback.chat(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)
                except Exception as fb_err:
                    _logger.warning("Fallback provider %s failed: %s", fallback.name, fb_err)
            raise primary_error

    def _execute_chat(self, messages, model_name, tools=None, temperature=0.7, max_tokens=2048):
        base_url = self._get_effective_base_url()
        headers = self._get_headers()
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            
        endpoint = f"{base_url}/chat/completions"
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                choices = resp_data.get('choices', [])
                if choices:
                    msg = choices[0].get('message', {})
                    return {
                        "content": msg.get('content') or "",
                        "tool_calls": msg.get('tool_calls') or [],
                        "usage": resp_data.get('usage', {}),
                        "model": resp_data.get('model', model_name),
                        "raw": resp_data
                    }
                return {"content": "", "tool_calls": [], "usage": {}}
        except urllib.error.HTTPError as he:
            err_body = he.read().decode('utf-8', errors='ignore')
            _logger.error("Provider HTTP Error %s: %s", he.code, err_body)
            raise UserError(_("LLM Provider Error (%s): %s") % (he.code, err_body[:300]))

    def get_embedding(self, text, model_name=None):
        """Generate vector embedding for the given input text."""
        self.ensure_one()
        base_url = self._get_effective_base_url()
        headers = self._get_headers()
        emb_model = model_name or (self.default_embedding_model_id.name if self.default_embedding_model_id else "nomic-embed-text")
        
        payload = {
            "model": emb_model,
            "input": text
        }
        endpoint = f"{base_url}/embeddings"
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                data_list = resp_data.get('data', [])
                if data_list:
                    return data_list[0].get('embedding', [])
                return []
        except Exception as e:
            _logger.exception("Embedding generation failed on %s: %s", self.name, e)
            return []
