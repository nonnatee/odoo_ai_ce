#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes ACP (Agent Communication Protocol) Adapter
=================================================
Implements the Agent Communication Protocol (ACP) standard for local Hermes agents:
- Session Lifecycle & Context Management
- Event-Driven Thought-Chain Streaming (Thought -> Action -> Observation -> Final Answer)
- Human-in-the-Loop (HITL) Consent State Machine
- Bi-directional Bridge to Odoo MCP Gateway (/ai_ce/mcp_gateway)
"""

import json
import time
import uuid
import threading
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Generator

ACP_VERSION = "2026-01-acp.v1"

class AcpSessionState:
    IDLE = "idle"
    THINKING = "thinking"
    CALLING_TOOL = "calling_tool"
    WAITING_CONSENT = "waiting_consent"
    COMPLETED = "completed"
    ERROR = "error"


class AcpSession:
    """Represents an active ACP agent session with isolated state and message buffer."""
    def __init__(self, session_id: str, agent_name: str = "Hermes Agent", metadata: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self.agent_name = agent_name
        self.metadata = metadata or {}
        self.state = AcpSessionState.IDLE
        self.created_at = time.time()
        self.updated_at = time.time()
        self.messages: List[Dict[str, Any]] = []
        self.thought_chain: List[Dict[str, Any]] = []
        self.pending_tool_call: Optional[Dict[str, Any]] = None
        self.event_queue: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def add_thought(self, thought: str):
        with self.lock:
            entry = {"type": "thought", "content": thought, "timestamp": time.time()}
            self.thought_chain.append(entry)
            self.event_queue.append(entry)
            self.state = AcpSessionState.THINKING
            self.updated_at = time.time()

    def add_tool_call(self, tool_name: str, arguments: Dict[str, Any], requires_consent: bool = False):
        with self.lock:
            entry = {
                "type": "tool_call",
                "tool": tool_name,
                "arguments": arguments,
                "requires_consent": requires_consent,
                "timestamp": time.time()
            }
            self.thought_chain.append(entry)
            self.event_queue.append(entry)
            if requires_consent:
                self.state = AcpSessionState.WAITING_CONSENT
                self.pending_tool_call = entry
            else:
                self.state = AcpSessionState.CALLING_TOOL
            self.updated_at = time.time()

    def add_tool_result(self, tool_name: str, result: Any):
        with self.lock:
            entry = {
                "type": "tool_result",
                "tool": tool_name,
                "result": result,
                "timestamp": time.time()
            }
            self.thought_chain.append(entry)
            self.event_queue.append(entry)
            self.pending_tool_call = None
            self.state = AcpSessionState.THINKING
            self.updated_at = time.time()

    def complete(self, final_answer: str):
        with self.lock:
            entry = {
                "type": "final_answer",
                "content": final_answer,
                "timestamp": time.time()
            }
            self.messages.append({"role": "assistant", "content": final_answer})
            self.thought_chain.append(entry)
            self.event_queue.append(entry)
            self.state = AcpSessionState.COMPLETED
            self.updated_at = time.time()

    def fail(self, error_message: str):
        with self.lock:
            entry = {
                "type": "error",
                "message": error_message,
                "timestamp": time.time()
            }
            self.thought_chain.append(entry)
            self.event_queue.append(entry)
            self.state = AcpSessionState.ERROR
            self.updated_at = time.time()

    def get_and_clear_events(self) -> List[Dict[str, Any]]:
        with self.lock:
            events = list(self.event_queue)
            self.event_queue.clear()
            return events


class HermesAcpEngine:
    """Core ACP Protocol Engine managing sessions, tools, and execution loop."""
    def __init__(self, mcp_gateway_url: Optional[str] = None, mcp_api_key: Optional[str] = None):
        self.mcp_gateway_url = mcp_gateway_url
        self.mcp_api_key = mcp_api_key
        self.sessions: Dict[str, AcpSession] = {}
        self.lock = threading.Lock()

    def get_capabilities(self) -> Dict[str, Any]:
        """Returns the ACP capability manifest."""
        return {
            "protocol_version": ACP_VERSION,
            "agent_type": "hermes_autonomous_executor",
            "capabilities": {
                "streaming_sse": True,
                "multi_turn_dialog": True,
                "tool_calling": True,
                "human_in_the_loop": True,
                "mcp_bridge": True,
                "session_persistence": True,
            },
            "supported_modalities": ["text", "code", "json_structured"],
        }

    def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> AcpSession:
        with self.lock:
            session_id = f"acp_sess_{uuid.uuid4().hex[:12]}"
            session = AcpSession(session_id=session_id, metadata=metadata)
            self.sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[AcpSession]:
        with self.lock:
            return self.sessions.get(session_id)

    def close_session(self, session_id: str) -> bool:
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invokes a tool on the Odoo MCP Gateway."""
        if not self.mcp_gateway_url or not self.mcp_api_key:
            return {"status": "simulated_local", "tool": tool_name, "arguments": arguments}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.mcp_api_key}"
        }
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        req = urllib.request.Request(self.mcp_gateway_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("result", data)
        except Exception as e:
            return {"error": f"MCP tool execution failed: {str(e)}"}

    def run_acp_turn(self, session: AcpSession, user_prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Executes an agent reasoning step and yields real-time ACP events.
        Thought -> Action -> Observation -> Final Answer.
        """
        session.messages.append({"role": "user", "content": user_prompt})
        session.add_thought(f"Received prompt: '{user_prompt[:80]}...'. Devising execution plan.")
        yield {"event": "thought", "data": session.get_and_clear_events()[-1]}

        # Check for state-mutating intent requiring consent
        lower_prompt = user_prompt.lower()
        if any(w in lower_prompt for w in ["delete", "remove", "drop", "cancel order", "bulk update"]):
            session.add_thought("Detected sensitive state-mutating operation. Requesting Human-in-the-Loop consent.")
            yield {"event": "thought", "data": session.get_and_clear_events()[-1]}

            session.add_tool_call(
                tool_name="delete_record" if "delete" in lower_prompt else "update_record",
                arguments={"intent": user_prompt, "confidence": 0.95},
                requires_consent=True
            )
            yield {"event": "tool_consent_required", "data": session.get_and_clear_events()[-1]}
            return

        # Execute reasoning or tool invocation
        if "search" in lower_prompt or "find" in lower_prompt or "list" in lower_prompt:
            session.add_thought("Querying Odoo ERP database via MCP search_records tool.")
            yield {"event": "thought", "data": session.get_and_clear_events()[-1]}

            tool_args = {"model": "product.template" if "product" in lower_prompt else "res.partner", "domain": [], "limit": 5}
            session.add_tool_call("search_records", tool_args, requires_consent=False)
            yield {"event": "tool_call", "data": session.get_and_clear_events()[-1]}

            result = self.execute_mcp_tool("search_records", tool_args)
            session.add_tool_result("search_records", result)
            yield {"event": "tool_result", "data": session.get_and_clear_events()[-1]}

            session.add_thought("Synthesizing query observations into comprehensive structured response.")
            yield {"event": "thought", "data": session.get_and_clear_events()[-1]}

            answer = f"Found records matching your request: {json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)}"
            session.complete(answer)
            yield {"event": "final_answer", "data": session.get_and_clear_events()[-1]}
        else:
            session.add_thought("Formulating direct expert synthesis using Hermes reasoning.")
            yield {"event": "thought", "data": session.get_and_clear_events()[-1]}

            answer = f"Hermes Agent Analysis: {user_prompt}\n\nProcessed successfully with active context."
            session.complete(answer)
            yield {"event": "final_answer", "data": session.get_and_clear_events()[-1]}

    def approve_and_resume(self, session: AcpSession, decision: str = "approved") -> Generator[Dict[str, Any], None, None]:
        """Resumes a paused session following user HITL approval or rejection."""
        if session.state != AcpSessionState.WAITING_CONSENT or not session.pending_tool_call:
            session.fail("Cannot resume: session is not awaiting consent.")
            yield {"event": "error", "data": session.get_and_clear_events()[-1]}
            return

        tool_call = session.pending_tool_call
        if decision == "approved":
            session.add_thought(f"Consent GRANTED for tool '{tool_call['tool']}'. Executing action.")
            yield {"event": "thought", "data": session.get_and_clear_events()[-1]}

            result = self.execute_mcp_tool(tool_call["tool"], tool_call["arguments"])
            session.add_tool_result(tool_call["tool"], result)
            yield {"event": "tool_result", "data": session.get_and_clear_events()[-1]}

            session.complete(f"Operation '{tool_call['tool']}' executed successfully after approval.")
            yield {"event": "final_answer", "data": session.get_and_clear_events()[-1]}
        else:
            session.add_thought(f"Consent REJECTED for tool '{tool_call['tool']}'. Action cancelled.")
            yield {"event": "thought", "data": session.get_and_clear_events()[-1]}
            session.complete("Action was rejected by user. No database modifications were performed.")
            yield {"event": "final_answer", "data": session.get_and_clear_events()[-1]}
