# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sidecar.hermes_acp_adapter import HermesAcpEngine, AcpSessionState

class TestHermesAcp(TransactionCase):

    def setUp(self):
        super().setUp()
        self.provider = self.env['ai_ce.provider'].create({
            'name': 'Test Local Hermes Provider',
            'service': 'hermes',
            'api_base': 'http://127.0.0.1:8765/v1',
            'priority': 5,
            'active': True,
        })
        self.model = self.env['ai_ce.model'].create({
            'name': 'hermes-3-llama-3.1',
            'provider_id': self.provider.id,
            'model_use': 'chat',
            'context_window': 16384,
            'supports_tools': True,
            'is_default': True,
        })
        self.sidecar = self.env['ai_ce.hermes_sidecar'].create({
            'name': 'Test Hermes Supervisor',
            'host': '127.0.0.1',
            'port': 8765,
            'auto_spawn': False,
            'active': True,
        })

    def test_acp_engine_capabilities(self):
        """Test ACP capability manifest structure."""
        engine = HermesAcpEngine()
        caps = engine.get_capabilities()
        self.assertEqual(caps['agent_type'], 'hermes_autonomous_executor')
        self.assertTrue(caps['capabilities']['streaming_sse'])
        self.assertTrue(caps['capabilities']['human_in_the_loop'])
        self.assertTrue(caps['capabilities']['tool_calling'])

    def test_acp_session_lifecycle(self):
        """Test creating an ACP session and executing a turn."""
        engine = HermesAcpEngine()
        session = engine.create_session(metadata={"user": "admin"})
        self.assertTrue(session.session_id.startswith("acp_sess_"))
        self.assertEqual(session.state, AcpSessionState.IDLE)

        # Run agent turn
        events = list(engine.run_acp_turn(session, "List all active customers in Odoo"))
        self.assertTrue(len(events) >= 2)
        self.assertEqual(session.state, AcpSessionState.COMPLETED)
        
        # Check thought chain
        event_types = [e["event"] for e in events]
        self.assertIn("thought", event_types)
        self.assertIn("final_answer", event_types)

    def test_acp_hitl_consent_approval(self):
        """Test ACP Human-in-the-Loop consent gate and approval flow."""
        engine = HermesAcpEngine()
        session = engine.create_session()

        # Prompt with state-mutating intent
        events = list(engine.run_acp_turn(session, "Please delete record 45 from product catalog"))
        self.assertEqual(session.state, AcpSessionState.WAITING_CONSENT)
        self.assertIsNotNone(session.pending_tool_call)

        # Approve and resume
        resume_events = list(engine.approve_and_resume(session, decision="approved"))
        self.assertEqual(session.state, AcpSessionState.COMPLETED)
        final_answer = next((e["data"]["content"] for e in resume_events if e["event"] == "final_answer"), "")
        self.assertIn("executed successfully", final_answer)

    def test_hermes_sidecar_supervisor_model(self):
        """Test Hermes Sidecar ORM methods."""
        self.assertTrue(self.sidecar.exists())
        self.assertEqual(self.sidecar.port, 8765)

        # Test script path resolution
        script_path = self.sidecar._get_runner_script_path()
        self.assertTrue(os.path.exists(script_path))

        # Test stop process
        res = self.sidecar.action_stop_process()
        self.assertEqual(self.sidecar.process_pid, 0)
        self.assertFalse(self.sidecar.is_running)
        self.assertEqual(self.sidecar.state, 'stopped')

    def test_hermes_provider_effective_url(self):
        """Test Hermes provider URL generation."""
        url = self.provider._get_effective_base_url()
        self.assertEqual(url, 'http://127.0.0.1:8765/v1')
