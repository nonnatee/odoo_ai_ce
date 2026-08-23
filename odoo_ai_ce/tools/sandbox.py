# -*- coding: utf-8 -*-
import json
import logging
import time
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def execute_sandboxed_tool(env, tool_record, arguments, commit=False):
    """
    Execute an ai_ce.tool within a transaction savepoint.
    If commit is False, the savepoint is rolled back after execution,
    guaranteeing that no database modifications persist.
    """
    start_time = time.time()
    result = None
    error = None
    
    try:
        if not commit:
            with env.cr.savepoint():
                result = tool_record.execute(arguments)
                # Intentionally raise an internal sentinel to trigger rollback while capturing result
                raise _SandboxRollbackException(result)
        else:
            result = tool_record.execute(arguments)
    except _SandboxRollbackException as sbe:
        result = sbe.result
    except Exception as e:
        error = str(e)
        _logger.exception("Error executing tool in sandbox: %s", tool_record.name)
    
    elapsed_ms = (time.time() - start_time) * 1000.0
    return {
        "tool_name": tool_record.name,
        "success": error is None,
        "result": result,
        "error": error,
        "execution_time_ms": elapsed_ms,
        "sandboxed": not commit
    }

class _SandboxRollbackException(Exception):
    def __init__(self, result):
        self.result = result
