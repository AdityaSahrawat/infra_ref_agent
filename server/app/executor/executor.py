"""
Kubernetes action executor.
Parses tool execution requests, looks up registered tools, executes them,
and returns structured execution results with timestamps and logs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.executor.tools import get_tool
from app.services.logger import get_logger

logger = get_logger(__name__)


def execute_tool(
    tool_name: str,
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Find tool -> Execute -> Return result.
    
    Payload example:
    {
        "tool": "restart_deployment",
        "args": {
            "deployment": "auth-api"
        }
    }
    """
    args = args or {}
    executed_at = datetime.now(timezone.utc).isoformat()

    logger.info("Executing tool '%s' with args %s", tool_name, args)

    tool_fn = get_tool(tool_name)
    if not tool_fn:
        error_msg = f"Tool '{tool_name}' is not registered in TOOLS registry."
        logger.error(error_msg)
        return {
            "success": False,
            "tool": tool_name,
            "args": args,
            "executed_at": executed_at,
            "result": None,
            "logs": "",
            "error": error_msg,
        }

    # Parameter alias normalization for robustness
    normalized_args = dict(args)
    if "deployment_name" in normalized_args and "deployment" not in normalized_args:
        normalized_args["deployment"] = normalized_args.pop("deployment_name")
    if "pod" in normalized_args and "pod_name" not in normalized_args:
        normalized_args["pod_name"] = normalized_args.pop("pod")

    import inspect
    sig = inspect.signature(tool_fn)
    has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    if not has_var_kw:
        valid_keys = set(sig.parameters.keys())
        call_args = {k: v for k, v in normalized_args.items() if k in valid_keys}
    else:
        call_args = normalized_args

    try:
        res = tool_fn(**call_args)
        success = res.get("success", True) if isinstance(res, dict) else True
        error = res.get("error") if isinstance(res, dict) else None
        logs = res.get("logs", "") if isinstance(res, dict) else ""

        return {
            "success": success,
            "tool": tool_name,
            "args": args,
            "executed_at": executed_at,
            "result": res,
            "logs": logs,
            "error": error,
        }
    except Exception as exc:
        logger.exception("Failed executing tool '%s'", tool_name)
        return {
            "success": False,
            "tool": tool_name,
            "args": args,
            "executed_at": executed_at,
            "result": None,
            "logs": "",
            "error": f"Execution error: {str(exc)}",
        }


def execute_action_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience wrapper accepting a dictionary containing 'tool' and 'args'."""
    tool_name = payload.get("tool") or payload.get("action_type") or payload.get("action")
    args = payload.get("args") or payload.get("action_payload") or {}
    
    if not tool_name:
        return {
            "success": False,
            "tool": "unknown",
            "args": args,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "logs": "",
            "error": "No 'tool' specified in execution payload.",
        }

    return execute_tool(tool_name=tool_name, args=args)
