# -*- coding: utf-8 -*-
{
    'name': 'Odoo AI Community Edition (AI Hub & Hermes Agent Integration)',
    'version': '19.0.1.1',
    'category': 'Productivity/Artificial Intelligence',
    'summary': 'Unified AI Hub, Local Hermes Agent Sidecar, Product Catalog Enrichment, Content Studio, CRM Intelligence & Zero-Trust Governance',
    'description': """
Odoo AI Community Edition (odoo_ai_ce)
======================================
Enterprise-grade AI Framework and Hermes Agent Integration for Odoo 19 CE:
* **Product Catalog Enrichment**: AI-generated SEO titles/meta, bullet highlights, and eCommerce descriptions.
* **Unified Hermes Content Studio**: Multi-channel copywriting for Mass Mailing, LINE Bot, Knowledge, and Social.
* **Autonomous CRM Lead Profiling**: Lead scoring (1-100), buying intent detection, and auto-drafted sales playbooks.
* **Asynchronous Batch Job Queue**: Non-blocking background workers with live progress tracking (`ai_ce.job`).
* **Multi-Provider Hub**: Ollama (local sovereign inference), OpenAI, Azure OpenAI, Anthropic Claude, and Gemini.
* **Local Hermes Sidecar**: Loopback IPC on 127.0.0.1:8765 with real-time SSE streaming.
* **Zero-Trust Security**: Human-in-the-loop consent queue, strict resource allowlist, and per-user audit logging.
    """,
    'author': 'Nonnatee Kanjana',
    'website': 'https://github.com/nonnatee/odoo_ai_ce',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'html_editor',
        'product',
        'crm',
    ],
    'data': [
        'security/ai_ce_security.xml',
        'security/ir.model.access.csv',
        'data/ai_ce_data.xml',
        'data/ai_ce_cron.xml',
        'wizard/ai_ce_test_tool_wizard_views.xml',
        'wizard/ai_ce_fetch_model_wizard_views.xml',
        'wizard/ai_ce_generate_key_wizard_views.xml',
        'wizard/ai_ce_product_enrich_views.xml',
        'wizard/ai_ce_content_studio_views.xml',
        'wizard/ai_ce_lead_enrich_views.xml',
        'views/ai_ce_provider_views.xml',
        'views/ai_ce_agent_views.xml',
        'views/ai_ce_tool_views.xml',
        'views/ai_ce_resource_views.xml',
        'views/ai_ce_session_views.xml',
        'views/ai_ce_consent_views.xml',
        'views/ai_ce_log_views.xml',
        'views/ai_ce_job_views.xml',
        'views/product_template_views.xml',
        'views/crm_lead_views.xml',
        'views/ai_ce_dashboard_views.xml',
        'views/ai_ce_hermes_sidecar_views.xml',
        'views/res_config_settings_views.xml',
        'views/ai_ce_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_ai_ce/static/src/scss/ask_ai.scss',
            'odoo_ai_ce/static/src/scss/ai_dashboard.scss',
            'odoo_ai_ce/static/src/scss/content_studio.scss',
            'odoo_ai_ce/static/src/js/ask_ai_modal.js',
            'odoo_ai_ce/static/src/js/ask_ai_modal.xml',
            'odoo_ai_ce/static/src/js/ask_ai_service.js',
            'odoo_ai_ce/static/src/js/html_editor_ai.js',
            'odoo_ai_ce/static/src/js/dashboard/ai_dashboard.js',
            'odoo_ai_ce/static/src/js/dashboard/ai_dashboard.xml',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
}
