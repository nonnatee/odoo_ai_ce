# -*- coding: utf-8 -*-
import inspect
import json
import logging

_logger = logging.getLogger(__name__)

# Registry mapping: tool_name -> metadata dict
_DECORATED_TOOLS = {}

def ai_ce_tool(name=None, description="", input_schema=None, requires_consent=False, group_xml_id=None):
    """
    Decorator to register an Odoo model method as an AI-callable tool.
    
    Usage:
        @api.model
        @ai_ce_tool(
            name="summarize_quotation",
            description="Extract total, line count, and payment state for a given sale order.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Database ID of the sale order"}
                },
                "required": ["order_id"]
            },
            requires_consent=False
        )
        def action_ai_summarize_quote(self, order_id):
            ...
    """
    def wrapper(func):
        tool_name = name or func.__name__
        schema = input_schema or _infer_schema_from_func(func)
        
        _DECORATED_TOOLS[tool_name] = {
            "name": tool_name,
            "func_name": func.__name__,
            "description": description or (inspect.getdoc(func) or "").strip(),
            "input_schema": schema,
            "requires_consent": requires_consent,
            "group_xml_id": group_xml_id,
        }
        func._ai_ce_tool_metadata = _DECORATED_TOOLS[tool_name]
        return func
    return wrapper

def _infer_schema_from_func(func):
    """Infer basic JSON Schema from function signature if not explicitly provided."""
    sig = inspect.signature(func)
    props = {}
    required = []
    for param_name, param in sig.parameters.items():
        if param_name in ('self', 'cr', 'uid', 'context'):
            continue
        props[param_name] = {"type": "string", "description": f"Parameter {param_name}"}
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    return {
        "type": "object",
        "properties": props,
        "required": required
    }

def get_registered_tools():
    """Return dictionary of all registered decorated tools."""
    return dict(_DECORATED_TOOLS)
