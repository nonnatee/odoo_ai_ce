# -*- coding: utf-8 -*-
import os
import re
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

DOC_TOPICS = [
    {
        "id": "index",
        "file": "index.md",
        "title": "Documentation Index & Overview",
        "category": "Getting Started",
        "icon": "fa-book",
        "description": "Master index and guide to all Odoo AI Community Edition manuals and references.",
        "reading_time": "2 min",
    },
    {
        "id": "module_overview",
        "file": "module_overview.md",
        "title": "Module Overview & Quick Start",
        "category": "Getting Started",
        "icon": "fa-compass",
        "description": "Technical dependencies, models index, wizards catalog, and high-level architecture overview.",
        "reading_time": "3 min",
    },
    {
        "id": "architecture",
        "file": "architecture.md",
        "title": "Architecture & Zero-Trust Security",
        "category": "Getting Started",
        "icon": "fa-cubes",
        "description": "Zero-trust security model, least-privilege scoping, HITL approval queue, and pgvector RAG.",
        "reading_time": "6 min",
    },
    {
        "id": "product_enrichment",
        "file": "product_enrichment.md",
        "title": "Product Catalog Enrichment",
        "category": "Business Operations",
        "icon": "fa-shopping-bag",
        "description": "Interactive before/after diff preview, multilingual copywriting (EN/TH/JA/ZH/DE/FR), and batch enrichment.",
        "reading_time": "5 min",
    },
    {
        "id": "content_studio",
        "file": "content_studio.md",
        "title": "Hermes Content Studio",
        "category": "Business Operations",
        "icon": "fa-paint-brush",
        "description": "Omni-channel marketing copy generator for Mass Mailing, LINE Bot Flex Messages, Knowledge Base, and Social.",
        "reading_time": "4 min",
    },
    {
        "id": "crm_intelligence",
        "file": "crm_intelligence.md",
        "title": "Autonomous CRM Lead Intelligence",
        "category": "Business Operations",
        "icon": "fa-line-chart",
        "description": "Company domain profiling, 1–100 qualification scoring, purchase intent detection, and sales playbooks.",
        "reading_time": "4 min",
    },
    {
        "id": "website_tools",
        "file": "website_tools.md",
        "title": "Website & E-Commerce AI Tools",
        "category": "Intelligent Tools",
        "icon": "fa-globe",
        "description": "Page inspection, live SEO metadata updates, responsive QWeb snippet generation, and live arch mutation.",
        "reading_time": "5 min",
    },
    {
        "id": "discuss_bot",
        "file": "discuss_bot.md",
        "title": "Odoo Discuss & Chat AI Integration",
        "category": "Intelligent Tools",
        "icon": "fa-comments-o",
        "description": "Virtual partner 'Hermes AI Agent', 1-on-1 direct messages, channel @mentions, and HITL approval badges in chatter.",
        "reading_time": "4 min",
    },
    {
        "id": "chat_prompts",
        "file": "chat_prompts.md",
        "title": "AI Chat Prompts & Playbook",
        "category": "Intelligent Tools",
        "icon": "fa-magic",
        "description": "Comprehensive library of ready-to-use prompt templates for Sales, CRM, Accounting, Inventory, Website, and Marketing.",
        "reading_time": "4 min",
    },
    {
        "id": "agent_use_cases",
        "file": "agent_use_cases.md",
        "title": "Autonomous Agent Use-Cases",
        "category": "Intelligent Tools",
        "icon": "fa-cogs",
        "description": "End-to-end multi-turn ReAct execution loops, database queries, and zero-trust HITL consent flows.",
        "reading_time": "5 min",
    },
    {
        "id": "mcp_gateway",
        "file": "mcp_gateway.md",
        "title": "Model Context Protocol (MCP) Gateway",
        "category": "Extensibility & MCP",
        "icon": "fa-plug",
        "description": "Streamable-HTTP JSON-RPC 2.0 gateway, Claude Desktop & Cursor IDE integration, and resource allowlists.",
        "reading_time": "6 min",
    },
    {
        "id": "hermes_sidecar",
        "file": "hermes_sidecar.md",
        "title": "Hermes Agent Sidecar & Job Queue",
        "category": "Extensibility & MCP",
        "icon": "fa-microchip",
        "description": "Local loopback daemon (127.0.0.1:8765), ACP supervisor control, asynchronous job queue (ai_ce.job), and live telemetry.",
        "reading_time": "5 min",
    },
    {
        "id": "configuration_security",
        "file": "configuration_security.md",
        "title": "Configuration, Security & Governance",
        "category": "Administration & Security",
        "icon": "fa-shield",
        "description": "Multi-provider configuration (Ollama, OpenAI, Claude, Gemini), tool sandboxing, and audit logs.",
        "reading_time": "5 min",
    },
]

class AiCeDocController(http.Controller):

    def _get_doc_dir(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'doc')

    @http.route('/ai_ce/documentation/topics', type='json', auth='user', methods=['POST'])
    def get_topics(self):
        """
        Return the list of all available documentation topics grouped by category.
        """
        categories = {}
        for topic in DOC_TOPICS:
            cat = topic['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(topic)

        return {
            "topics": DOC_TOPICS,
            "categories": categories,
        }

    @http.route('/ai_ce/documentation/content', type='json', auth='user', methods=['POST'])
    def get_content(self, doc_id="index"):
        """
        Return raw markdown content and extracted table of contents headings for a given topic ID.
        """
        topic = next((t for t in DOC_TOPICS if t['id'] == doc_id), None)
        if not topic:
            topic = DOC_TOPICS[0]

        doc_dir = self._get_doc_dir()
        file_path = os.path.join(doc_dir, topic['file'])

        content = ""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = f"# Documentation Not Found\n\nThe requested document `{topic['file']}` could not be located on the server."

        # Extract headings for on-page quick jump navigation
        headings = []
        for line in content.split('\n'):
            match = re.match(r'^(#{1,4})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                # Clean text of markdown links or badges
                clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
                clean_text = re.sub(r'[*`_]', '', clean_text)
                anchor = re.sub(r'[^a-zA-Z0-9]+', '-', clean_text.lower()).strip('-')
                headings.append({
                    "level": level,
                    "text": clean_text,
                    "anchor": anchor
                })

        return {
            "topic": topic,
            "content": content,
            "headings": headings,
        }

    @http.route('/ai_ce/doc/<string:topic_id>', type='http', auth='user', methods=['GET'])
    def view_doc_http(self, topic_id='index'):
        """
        Standalone HTML documentation reader endpoint.
        """
        topic = next((t for t in DOC_TOPICS if t['id'] == topic_id), None)
        if not topic:
            topic = DOC_TOPICS[0]

        doc_dir = self._get_doc_dir()
        file_path = os.path.join(doc_dir, topic['file'])
        content = ""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8"/>
            <title>{topic['title']} - Odoo AI Documentation</title>
            <link rel="stylesheet" href="/web/static/lib/fontawesome/css/font-awesome.css"/>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #2d3748; background: #f8fafc; padding: 2rem; max-width: 960px; margin: 0 auto; }}
                h1, h2, h3 {{ color: #1a202c; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3rem; margin-top: 1.5rem; }}
                pre {{ background: #1e293b; color: #f8fafc; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
                code {{ font-family: monospace; background: #e2e8f0; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.9em; }}
                pre code {{ background: transparent; padding: 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
                th, td {{ border: 1px solid #cbd5e1; padding: 0.5rem 0.75rem; text-align: left; }}
                th {{ background: #f1f5f9; }}
                .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 9999px; background: #714B67; color: white; font-size: 0.8rem; }}
            </style>
        </head>
        <body>
            <div style="margin-bottom: 2rem; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge"><i class="fa fa-book"></i> {topic['category']}</span>
                    <h1 style="margin: 0.5rem 0 0 0; border-bottom: none;">{topic['title']}</h1>
                </div>
                <a href="/odoo/action-odoo_ai_ce_dashboard" style="text-decoration: none; color: #714B67; font-weight: bold;">← Back to AI Hub</a>
            </div>
            <pre style="white-space: pre-wrap; word-break: break-word; background: #ffffff; color: #1e293b; border: 1px solid #e2e8f0;">{content}</pre>
        </body>
        </html>
        """
        return Response(html_body, content_type='text/html; charset=utf-8')
