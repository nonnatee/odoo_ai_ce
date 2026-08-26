# -*- coding: utf-8 -*-
import json
import logging
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

def execute_builtin_tool(env, tool_name, arguments, user_id=None):
    """
    Execute a standard built-in ORM tool under the security context of the given user or env.
    """
    target_env = env(user=user_id) if user_id else env
    
    if tool_name == "search_records":
        return _builtin_search_records(target_env, arguments)
    elif tool_name == "create_record":
        return _builtin_create_record(target_env, arguments)
    elif tool_name == "update_record":
        return _builtin_update_record(target_env, arguments)
    elif tool_name == "unlink_record" or tool_name == "delete_record":
        return _builtin_unlink_record(target_env, arguments)
    elif tool_name == "analyze_records":
        return _builtin_analyze_records(target_env, arguments)
    elif tool_name == "website_inspect_page":
        from .website_tools import execute_website_inspect_page
        return execute_website_inspect_page(target_env, arguments)
    elif tool_name == "website_update_seo":
        from .website_tools import execute_website_update_seo
        return execute_website_update_seo(target_env, arguments)
    elif tool_name == "website_generate_snippet":
        from .website_tools import execute_website_generate_snippet
        return execute_website_generate_snippet(target_env, arguments)
    elif tool_name == "website_mutate_page_arch":
        from .website_tools import execute_website_mutate_page_arch
        return execute_website_mutate_page_arch(target_env, arguments)
    elif tool_name == "ecommerce_enrich_product_page":
        from .website_tools import execute_ecommerce_enrich_product_page
        return execute_ecommerce_enrich_product_page(target_env, arguments)
    else:
        raise UserError(f"Unknown built-in tool: {tool_name}")

def _validate_model_access(env, model_name):
    """Ensure the model exists and is permitted in the ai_ce.resource allowlist."""
    if model_name not in env:
        raise UserError(f"Model '{model_name}' does not exist in this database.")
    
    # Check resource allowlist if configured
    resource_model = env['ai_ce.resource'].sudo().search([
        ('model_name', '=', model_name),
        ('active', '=', True)
    ], limit=1)
    
    # If resource model exists and strict allowlist is enabled, verify exposure
    if not resource_model:
        # Check system parameter for strict allowlist enforcement
        strict = env['ir.config_parameter'].sudo().get_param('odoo_ai_ce.strict_allowlist', 'True') == 'True'
        if strict and not env.user.has_group('base.group_system'):
            raise AccessError(f"Access to model '{model_name}' is restricted by AI Resource policy.")

def _builtin_search_records(env, args):
    model_name = args.get("model")
    domain = args.get("domain") or []
    fields = args.get("fields") or []
    limit = int(args.get("limit") or 20)
    limit = min(limit, 200) # Enforce safety ceiling
    
    _validate_model_access(env, model_name)
    records = env[model_name].search_read(domain, fields=fields if fields else None, limit=limit)
    return {
        "model": model_name,
        "count": len(records),
        "records": records
    }

def _builtin_create_record(env, args):
    model_name = args.get("model")
    values = args.get("values") or {}
    
    _validate_model_access(env, model_name)
    record = env[model_name].create(values)
    return {
        "model": model_name,
        "id": record.id,
        "display_name": record.display_name,
        "created": True
    }

def _builtin_update_record(env, args):
    model_name = args.get("model")
    ids = args.get("ids") or []
    if isinstance(ids, int):
        ids = [ids]
    values = args.get("values") or {}
    
    _validate_model_access(env, model_name)
    records = env[model_name].browse(ids)
    records.write(values)
    return {
        "model": model_name,
        "updated_ids": ids,
        "success": True
    }

def _builtin_unlink_record(env, args):
    model_name = args.get("model")
    ids = args.get("ids") or []
    if isinstance(ids, int):
        ids = [ids]
    
    _validate_model_access(env, model_name)
    records = env[model_name].browse(ids)
    records.unlink()
    return {
        "model": model_name,
        "deleted_ids": ids,
        "success": True
    }

def _builtin_analyze_records(env, args):
    model_name = args.get("model")
    question = args.get("question")
    domain = args.get("domain") or []
    fields = args.get("fields") or []
    limit = int(args.get("limit") or 20)
    
    _validate_model_access(env, model_name)
    records = env[model_name].search_read(domain, fields=fields if fields else None, limit=limit)
    
    # Return formatted payload ready for agent synthesis
    return {
        "model": model_name,
        "question": question,
        "sample_count": len(records),
        "data_payload": records
    }
