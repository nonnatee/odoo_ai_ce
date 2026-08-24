# Hermes Agent Sidecar & ACP (Agent Communication Protocol) Supervisor

The **Hermes Agent Sidecar** is a local autonomous agent runtime and subprocess daemon that runs alongside Odoo on loopback `127.0.0.1:8765`.

It provides three core capabilities:
1. **Agent Communication Protocol (ACP) Engine (`hermes-acp`)**: Stateful agent sessions, step-by-step reasoning thought chains, Human-in-the-Loop (HITL) consent state machines, and native bridge to Odoo's MCP Gateway (`/ai_ce/mcp_gateway`).
2. **OpenAI-Compatible Chat Completions (`/v1/chat/completions`)**: Exposes standard OpenAI completions with function calling, allowing Hermes models (`hermes-3-llama-3.1`) to act as a first-class AI Provider in Odoo.
3. **Subprocess Supervisor**: Odoo-managed lifecycle (auto-spawn, start, stop, restart, PID/memory telemetry) with multithreaded background job execution.

---

## 🏗️ Architecture & Protocol Stack

```mermaid
graph TD
    subgraph Odoo 19 CE Web Client & Backend
        UI[Ask AI Dialog / AI Dashboard / OWL 3]
        ORM[ai_ce.hermes_sidecar / ai_ce.provider]
        MCP[MCP Gateway /ai_ce/mcp_gateway]
        Job[Batch Job Queue ai_ce.job]
    end

    subgraph Local Hermes Daemon (:8765)
        Supervisor[Process Supervisor & Telemetry]
        OpenAI[/v1/chat/completions OpenAI Endpoint]
        ACP[Hermes ACP Engine & Session Manager]
        Pool[Multithreaded Task Worker Pool]
    end

    subgraph LLM Backend
        Ollama[Local Ollama / vLLM / Nous Hermes]
    end

    UI -->|Ask AI & Live Thoughts| ORM
    UI -->|Start / Stop / Restart| ORM
    ORM -->|Subprocess Control & Health| Supervisor
    ORM -->|OpenAI Chat Request| OpenAI
    ORM -->|ACP Prompt & Streaming| ACP
    ACP -->|Tool Invocations| MCP
    Job -->|Submit Batch Tasks| Pool
    Pool -->|Webhook Progress Checkpoints| Job
    OpenAI --> Ollama
    ACP --> Ollama
```

---

## 📡 API Specifications

### 1. Process Telemetry (`GET /health` or `GET /status`)
```bash
curl http://127.0.0.1:8765/health
```
Response:
```json
{
  "status": "healthy",
  "version": "19.0.2.0-hermes-acp",
  "telemetry": {
    "pid": 14220,
    "uptime_seconds": 1240,
    "memory_mb": 42.5,
    "cpu_percent": 0.4,
    "active_threads": 4,
    "active_acp_sessions": 1,
    "active_tasks_count": 0
  },
  "acp_capabilities": {
    "protocol_version": "2026-01-acp.v1",
    "agent_type": "hermes_autonomous_executor",
    "capabilities": {
      "streaming_sse": true,
      "multi_turn_dialog": true,
      "tool_calling": true,
      "human_in_the_loop": true,
      "mcp_bridge": true,
      "session_persistence": true
    }
  }
}
```

### 2. OpenAI-Compatible Chat (`POST /v1/chat/completions`)
```bash
curl -X POST http://127.0.0.1:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hermes-3-llama-3.1",
    "messages": [
      {"role": "system", "content": "You are Hermes."},
      {"role": "user", "content": "Explain CRM qualification scoring."}
    ]
  }'
```

### 3. ACP Session Management (`POST /v1/acp/sessions/create`)
```bash
curl -X POST http://127.0.0.1:8765/v1/acp/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"user_id": 1}}'
```
Response:
```json
{
  "session_id": "acp_sess_8f3d1e4c92ab",
  "status": "created",
  "capabilities": { ... }
}
```

### 4. ACP Turn Execution (`POST /v1/acp/sessions/<id>/prompt`)
Streams thought events, tool calls, and final answers over SSE or structured JSON.

---

## 🛠️ Odoo Supervisor Controls

Administrators can manage the local Hermes agent directly from Odoo:
1. **AI Hub > Configuration > Hermes Supervisor**:
   - **Start Daemon**: Spawns detached daemon using the configured Python interpreter.
   - **Restart Daemon**: Performs a clean restart.
   - **Stop Daemon**: Gracefully halts the background process.
   - **Health Check**: Pings `/health` and records live RAM/CPU metrics.
2. **AI Control Center Dashboard**: Live telemetry widget with single-click start/stop and real-time status indicators.
