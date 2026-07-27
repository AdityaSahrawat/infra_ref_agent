"""
Tool registry module for Kubernetes action tools.
"""

from typing import Any, Callable, Dict, Optional
from app.executor.kubernetes import (
    delete_pod,
    get_pod_logs,
    get_pod_status,
    list_pods,
    restart_deployment,
    scale_deployment,
    verify_deployment_health,
)

TOOLS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "restart_deployment": restart_deployment,
    "scale_deployment": scale_deployment,
    "delete_pod": delete_pod,
    "get_pod_logs": get_pod_logs,
    "list_pods": list_pods,
    "get_pod_status": get_pod_status,
    "verify_deployment_health": verify_deployment_health,
}


def get_tool(tool_name: str) -> Optional[Callable[..., Dict[str, Any]]]:
    """Retrieve a registered tool function by name."""
    return TOOLS.get(tool_name)


def list_tools() -> Dict[str, str]:
    """Return dictionary of available tool names and docstrings."""
    return {name: (func.__doc__ or "").strip() for name, func in TOOLS.items()}
