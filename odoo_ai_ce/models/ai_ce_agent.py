# -*- coding: utf-8 -*-
import json
import logging
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AiCeAgent(models.Model):
    _name = "ai_ce.agent"
    _description = "AI Autonomous Agent Engine"
    _order = "name asc"

    name = fields.Char(string="Agent Name", required=True)
    description = fields.Text(string="Role & Scope Description")
    
    provider_id = fields.Many2one("ai_ce.provider", string="LLM Provider", required=True)
    model_id = fields.Many2one("ai_ce.model", string="Model", domain="[('provider_id', '=', provider_id), ('model_use', '=', 'chat')]")
    
    system_prompt = fields.Text(string="System Prompt", required=True, default="You are an intelligent, helpful AI Assistant embedded in Odoo ERP. You have access to database tools to assist users with business operations, document summarization, and data queries.")
    tool_ids = fields.Many2many("ai_ce.tool", "ai_ce_agent_tool_rel", "agent_id", "tool_id", string="Allowed Tools")
    
    temperature = fields.Float(string="Temperature", default=0.3, help="Lower values produce more deterministic, precise reasoning")
    max_iterations = fields.Integer(string="Max Reasoning Turns", default=8, help="Safety limit for multi-turn tool loops")
    restrict_to_sources = fields.Boolean(string="Strict RAG Grounding", default=False, help="Instruct agent to only answer from retrieved knowledge chunks")
    active = fields.Boolean(string="Active", default=True)

    def run_agent(self, user_prompt, session=None, record_context=None, user_id=None):
        """
        Execute the autonomous multi-turn agent reasoning loop.
        """
        self.ensure_one()
        caller_uid = user_id or self.env.uid
        start_time = time.time()
        
        # 1. Initialize or load conversation session
        if not session:
            session = self.env['ai_ce.session'].create({
                'name': f"Session {fields.Datetime.now()}",
                'agent_id': self.id,
                'user_id': caller_uid,
            })
            
        # 2. Build contextual prompt with Active Record & RAG
        context_parts = []
        if record_context:
            context_parts.append(f"### Current Record Context:\n{json.dumps(record_context, indent=2, default=str)}")
            
        # Retrieve vector embeddings RAG
        relevant_chunks = self.env['ai_ce.vector.chunk'].search_similar(
            user_prompt, provider=self.provider_id, limit=3
        )
        if relevant_chunks:
            rag_text = "\n\n".join([f"Source [{c['res_model']}:{c['res_id']}]:\n{c['text']}" for c in relevant_chunks])
            context_parts.append(f"### Retrieved Grounded Knowledge:\n{rag_text}")
            
        # Assemble message history
        messages = [{"role": "system", "content": self.system_prompt}]
        if context_parts:
            messages.append({"role": "system", "content": "\n\n".join(context_parts)})
            
        # Append existing session history
        messages.extend(session.get_formatted_history())
        # Append latest user prompt
        messages.append({"role": "user", "content": user_prompt})
        session.add_message("user", user_prompt)
        
        # Prepare OpenAI-compatible tools schema
        tools_schema = [t.to_openai_tool_schema() for t in self.tool_ids.filtered('active')]
        
        iteration = 0
        final_answer = ""
        last_tool_id = False
        
        while iteration < self.max_iterations:
            iteration += 1
            _logger.info("Agent %s turn %d executing...", self.name, iteration)
            
            # Call provider
            model_name = self.model_id.name if self.model_id else None
            response = self.provider_id.chat(
                messages=messages,
                model_name=model_name,
                tools=tools_schema if tools_schema else None,
                temperature=self.temperature
            )
            
            content = response.get('content') or ""
            tool_calls = response.get('tool_calls') or []
            
            if not tool_calls:
                # Agent completed reasoning, final answer reached
                final_answer = content
                session.add_message("assistant", final_answer)
                break
                
            # Process tool calls
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls
            })
            
            for call in tool_calls:
                func_obj = call.get('function', {})
                tool_name = func_obj.get('name')
                tool_args_str = func_obj.get('arguments', '{}')
                try:
                    tool_args = json.loads(tool_args_str) if isinstance(tool_args_str, str) else tool_args_str
                except Exception:
                    tool_args = {}
                    
                tool_record = self.tool_ids.filtered(lambda t: t.name == tool_name)
                if not tool_record:
                    tool_output = {"error": f"Tool '{tool_name}' is not authorized for this agent."}
                else:
                    last_tool_id = tool_record.id
                    try:
                        tool_output = tool_record.execute(tool_args, user_id=caller_uid, session_id=session.id)
                    except Exception as e:
                        _logger.exception("Error executing tool %s", tool_name)
                        tool_output = {"error": str(e)}
                        
                # Append tool response
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": call.get('id', 'call_0'),
                    "name": tool_name,
                    "content": json.dumps(tool_output, default=str)
                }
                messages.append(tool_msg)
                session.add_message("tool", json.dumps(tool_output, default=str), tool_call_id=call.get('id'))
                
                # If tool required consent, pause execution
                if isinstance(tool_output, dict) and tool_output.get("_status") == "consent_required":
                    final_answer = f"⚠️ Tool `{tool_name}` requires user approval before execution. Pending approval request #{tool_output.get('consent_id')} has been created."
                    session.add_message("assistant", final_answer)
                    break

        if not final_answer and iteration >= self.max_iterations:
            final_answer = "⚠️ Agent reached maximum reasoning turns without producing a final answer."
            session.add_message("assistant", final_answer)

        elapsed_ms = (time.time() - start_time) * 1000.0
        
        # Log to audit trail
        self.env['ai_ce.log'].create({
            'user_id': caller_uid,
            'client_type': 'web',
            'tool_id': last_tool_id,
            'model_used': self.model_id.name if self.model_id else self.provider_id.name,
            'execution_time_ms': elapsed_ms,
            'input_preview': user_prompt[:400],
            'status': 'success' if final_answer else 'error',
        })
        
        return {
            "session_id": session.id,
            "answer": final_answer,
            "iterations": iteration,
            "execution_time_ms": elapsed_ms
        }
